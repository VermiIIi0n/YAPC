"""Command interface for YAPC."""

import os
import sys
import asyncio
import ujson as json
import argparse
import yaml
import httpx
import time
import pullers
import git
import notification as notify
from datetime import datetime
from urllib.request import getproxies
from getpass import getpass
from selenium import webdriver
from rich.progress import Progress
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.common.by import By
from crawler import PixivCrawler
from utils import real_dir, real_path, ObjDict, version_cmp
from utils import SideLogger, MonoLogger, selenium_cookies_to_jar as s2j

#####################

# Check config file
if not os.path.exists(real_path("./config.yaml")):
    if not os.path.exists(real_path("./default.yaml")):
        raise FileNotFoundError("Default config file not found.")
    with open(real_path("./default.yaml"), "r") as f:
        _c = f.read()
        _c = '\n'.join(_c.split('\n')[3:])
        with open(real_path("./config.yaml"), "w") as f2:
            f2.write(_c)
    print(" Config file 'config.yaml' generated. "
          "Please edit it before running again.")
    sys.exit(0)

# Make dirs
if not os.path.exists(real_path("./data")):
    os.mkdir(real_path("./data"))

# Config version check
MIN_CFG_V = "0.1.0"
with open(real_path("./default.yaml"), "r") as f:
    config: ObjDict = ObjDict(yaml.safe_load(f))
with open(real_path("./config.yaml"), "r") as f:
    for k, v in yaml.safe_load(f).items():
        config[k].update(v)

#####################

# Parse args
parser = argparse.ArgumentParser(
    prog="YAPC", description="YAPC - Yet Another Pixiv Crawler")
parser.add_argument("--username", "-u", type=str,
                    help="Username for Pixiv account.")
parser.add_argument("--password", "-p", type=str,
                    help="Password for Pixiv account.")
parser.add_argument("--target", "-t", type=str, help="Target user ID.")
parser.add_argument("--overwrite", "-O", action="store_true",
                    help="Overwrite existing files.")
parser.add_argument("--start", "-S", type=int,
                    help="Start offset for Pixiv account.")
parser.add_argument("--stop", "-E", type=int,
                    help="End offset for Pixiv account.")
parser.add_argument("--debug", "-d", action="store_true",
                    help="Enable debugging mode")
parser.add_argument("--console", "-c", action="store_true",
                    help="Show logs in console")
parser.add_argument("--backend", "-b", type=str, choices=("tinyend",
                    "mongoend"), help="Backend for Pixiv account.")
parser.add_argument("--path", "-P", type=str,
                    help="Database path, a MongoDB URI or a TinyDB file path.")
parser.add_argument("--proxy", type=str, default='',
                    help="Proxy for Pixiv account. e.g. http://127.0.0.1:2333")
parser.add_argument("--version", "-v", action="store_true",
                    help="Show version and exit.")

args = parser.parse_args()
username = args.username or config.pixiv.username
password = args.password or config.pixiv.password
uid = args.target or config.pixiv.target
overwrite = args.overwrite or config.puller.overwrite
start = args.start or config.pixiv.offsets.start
stop = args.stop or config.pixiv.offsets.stop
log_level = "DEBUG" if args.debug else config.logging.level.upper()
console = args.console or config.logging.console
log_path = real_path(config.logging.path)
backend = args.backend or config.database.backend
path = args.path or config.database.path
if not os.path.exists(real_dir(path)):
    os.makedirs(real_dir(path))
match args.proxy.split("://"):
    case ["http", proxy] | ["https://", proxy]:
        proxies = {"http://": proxy, "https://": proxy}
    case ["socks5", proxy]:
        proxies = {"socks5://": proxy}
    case ["all", proxy]:
        proxies = {"http://": proxy, "https://": proxy, "socks5://": proxy}
    case ['']:
        proxies = {
            k+"://": v for k, v in
            (config.puller.proxies or getproxies()).items()}
    case _:
        raise ValueError("Invalid proxy format.")

#####################

# Logging
logger = SideLogger(MonoLogger(level=log_level, to_console=console,
                    path=log_path, formatter=config.logging.format,))

# Prepare notifications
if config.notification.enable:
    opts: ObjDict = config.notification.copy()
    opts.pop("enable")
    on_success: bool = opts.pop("on_success")
    on_failure: bool = opts.pop("on_failure")
    notifiers: list = []
    for handler, h_opts in opts.items():
        if not h_opts.pop("enable"):
            continue
        notifier = getattr(notify, handler)
        notifier.init(**h_opts)
        notifiers.append(notifier)

    def uncaught_exc(exc_type, exc_value, exc_traceback):
        """A helper function to catch uncaught exceptions."""
        logger.exception("Uncaught exception", exc_info=(
            exc_type, exc_value, exc_traceback))
        logger.join()
        if on_failure:
            for n in notifiers:
                n.on_failure(exc_type, exc_value, exc_traceback, config)

    sys.excepthook = uncaught_exc

    def notify_success(*args):
        if on_success:
            for n in notifiers:
                n.on_success(*args, config)
else:
    def notify_success(*args):
        ...  # Do nothing when notification is disabled

##################################################
###################### Main ######################


async def main():
    with open(real_path("./meta.json")) as f:
        meta = ObjDict(json.load(f))
        if args.version:
            print(meta.version)
            sys.exit(0)
        try:
            r = httpx.get(
                "https://raw.githubusercontent.com/"
                f"{meta.author}/YAPC/{meta.branch}/meta.json",
                proxies=proxies)
            r = ObjDict(json.loads(r.text))
            if version_cmp(meta.version, r.version) < 0:
                print("**********************************\n"
                      " A new version is available.\n" +
                      f" Currenct version: {meta.version}\n" +
                      f" Latest version: {r.version}\n" +
                      "**********************************\n")
        except Exception:  # skipcq: PYL-W0703
            print("Failed to check for updates.")

    cookies_path = real_path("./data/cookies.json")
    if os.path.exists(cookies_path):
        with open(real_path(cookies_path), "r+") as f:
            r_cookies: dict[str, str] = json.load(f)
            cookies = s2j(r_cookies)
            r = httpx.get("https://www.pixiv.net/setting_user.php",
                          follow_redirects=False, cookies=cookies, timeout=20,
                          headers=config.puller.headers, proxies=proxies)
            if r.status_code != 200:
                logger.debug(f"return code {r.status_code}\n"+r.text)
                logger.info("Cookies expired.")
                r_cookies = login(username, password)
                if config.pixiv.save_cookies:
                    f.seek(0)
                    f.truncate()
                    json.dump(r_cookies, f, indent=2)
                    logger.info("Cookies saved.")
    else:
        logger.info("Cookies not found.")
        r_cookies = login(username, password)
        if config.pixiv.save_cookies:
            with open(real_path(cookies_path), "w") as f:
                json.dump(r_cookies, f, indent=2)
                logger.info("Cookies saved.")
    cookies = s2j(r_cookies)

    match backend:
        case "tinyend":
            lib_args = config.database.tinyend
        case "mongoend":
            lib_args = config.database.mongoend

    ascend = config.pixiv.offsets.ascend
    private = config.pixiv.private
    tag = config.pixiv.tag
    interval = config.puller.interval
    timeout = config.puller.timeout
    retry = config.puller.retry
    deleted = 0
    global uid
    datapath = real_path(config.puller.path)
    if not os.path.exists(datapath):
        os.makedirs(datapath)

    crawler = PixivCrawler(backend, path, datapath, cookies, uid,
                           config.puller.headers, proxies,
                           logger=logger, overwrite=overwrite,
                           timeout=timeout, retry=retry, interval=interval,
                           pixiv_host=config.pixiv.host, lib_args=lib_args)
    # Preparation
    lib_before = str(crawler.lib)
    print(lib_before)
    uid = uid or await crawler.fetch_uid()
    print(f"Target UID: {uid}")
    show_progress(crawler)
    pullers.Modifier.add_logging(crawler.puller, logger=logger)
    pullers.Modifier.raise_for_status(crawler.puller)
    pullers.Modifier.ignore_file_exists(crawler.puller)
    # Track the number of deleted works

    @crawler.on.deleted.work
    async def on_deleted(ev, crawler, pid):
        nonlocal deleted
        deleted += 1

    # Link start!
    await crawler.crawl_bookmarks(uid, start, stop, ascend, private, tag)

    print(f"Found {deleted} deleted work{'s' * (deleted>1)}.")

    lib_after = str(crawler.lib)
    print(lib_after)
    await crawler.close()

    # Git commit
    if backend == "tinyend" and config.git.enable:
        git_dir = real_dir(path)
        if not os.path.exists(os.path.join(git_dir, ".git")):
            git.Repo.init(git_dir, mkdir=True, initial_branch="master")
        repo = git.Repo(git_dir)
        repo.git.add(real_path(path))
        try:
            repo.git.commit("-m", f"Update: {datetime.now().date()}")
        except git.GitCommandError as e:
            if "Your branch is up to date" not in str(e):
                raise e  # Raise if not "nothing to commit"

        if config.git.remote:
            try:
                repo.delete_remote("lib")
            except git.GitCommandError:
                ...
            repo.create_remote("lib", config.git.remote)
            repo.git.push("-u", "lib", "master")

    notify_success(lib_before, lib_after, deleted)
    logger.join()

#################### End Main ####################
##################################################


def show_progress(crawler: PixivCrawler):
    """A helper function to show progress of the crawler."""
    @crawler.on.crawl.bookmark
    async def init(ev, crawler, uid, start, stop, ascend, private, tag):
        progress = Progress(refresh_per_second=30)
        progress.start()
        task = progress.add_task("Crawling", total=abs(stop-start))
        pullers.Modifier.show_progress(crawler.puller, progress=progress)

        @crawler.on.finish.work
        @crawler.on.deleted.work
        async def incre(ev, crawler, pid):
            progress.update(task, advance=1)


def login(username: str = '', password: str = '') -> list[dict[str, str]]:
    """Returns a list of Selenium cookies."""
    if (not username or not password) and args.headless:
        raise ValueError("Headless mode requires username and password" +
                         " when cookies are invalid")
    print("DO NOT MANUALLY CLOSE THE WINDOW!")
    while not username:
        username = input("Username: ")
    while not password:
        password = getpass(prompt="Password: ")

    driver_map = {
        "chrome": webdriver.Chrome,
        "firefox": webdriver.Firefox,
        "edge": webdriver.Edge,
        "safari": webdriver.Safari,
    }

    _exe_path = real_path(config.webdriver.path)
    if _exe_path:
        driver = driver_map[config.webdriver.browser](
            executable_path=_exe_path)
    else:
        driver = driver_map[config.webdriver.browser]()

    cookies_url = "https://www.pixiv.net/setting_user.php"
    try:
        driver.get(cookies_url)
        driver.find_element(
            by=By.CLASS_NAME, value="signup-form__submit--login").click()
        driver.find_element(by=By.XPATH,
            value="//input[@autocomplete=\"username\"] ").send_keys(username)
        driver.find_element(by=By.XPATH,
            value="//input[@autocomplete=\"current-password\"]").send_keys(password)
        driver.find_element(by=By.XPATH,
            value="//button[text()='Login']").click()

        time.sleep(1)
        raw = driver.get_cookies()
        t = 0
        while "first_visit_datetime_pc" not in {r["name"] for r in raw}:
            time.sleep(0.5)
            raw = driver.get_cookies()
            t += 1
            if t > 60:
                raise TimeoutError("Login failed. Cookies fetching timeout.")
        driver.close()
        return raw
    except NoSuchWindowException as e:
        logger.error(
            f"Window is probably closed by user before getting cookies: {e}")
        raise e


# Run main
asyncio.run(main())
