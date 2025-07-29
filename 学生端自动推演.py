import concurrent.futures
import time
import socket
import keyboard  # 用于监听键盘事件
from docutils.nodes import document
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
import random

# 目标网页的基本URL
base_url = "http://172.18.75.33:8001"

# 登录凭证
USERNAME = "Rafik"
PASSWORD = "777777777"

# 重试次数
MAX_ATTEMPTS = 3

# 连接超时设置（秒）
CONNECTION_TIMEOUT = 10


def check_server_connection(host, port, timeout=10):
    """检查服务器是否可以连接"""
    try:
        print(f"正在检查服务器 {host}:{port} 的连接...")
        socket.create_connection((host, port), timeout=timeout)
        print("服务器可以连接")
        return True
    except OSError as e:
        print(f"无法连接到服务器: {e}")
        return False


def initialize_driver():
    """初始化WebDriver并返回"""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-extensions")  # 禁用扩展减少启动时间
    options.add_argument("--disable-gpu")  # 禁用GPU加速
    options.add_argument("--no-sandbox")  # 沙盒模式禁用
    return webdriver.Chrome(options=options)


def login(driver):
    """执行登录操作"""
    for attempt in range(MAX_ATTEMPTS):
        print(f"尝试登录 (第{attempt + 1}/{MAX_ATTEMPTS}次)...")
        try:
            driver.get(base_url)

            # 等待用户名输入框加载完成
            username_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_input.send_keys(USERNAME)
            time.sleep(1)  # 输入后等待1秒

            # 输入密码
            password_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            password_input.send_keys(PASSWORD)
            time.sleep(1)  # 输入后等待1秒

            # 点击提交按钮
            submit_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
            )
            submit_button.click()
            time.sleep(1)  # 点击后等待1秒

            WebDriverWait(driver, 15).until(EC.url_changes(base_url))
            print("登录成功！")
            return True
        except (TimeoutException, NoSuchElementException) as e:
            print(f"登录过程中发生错误: {e}")
            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(2)
            else:
                return False


def perform_post_login_actions(driver):
    """登录成功后执行后续操作"""
    try:
        # 优化：使用显式等待替代固定sleep，增加模态框处理
        def click_element(selector, by=By.CSS_SELECTOR, name=None, check_modal=True):
            # 检查并关闭可能存在的模态框
            if check_modal:
                try:
                    # 等待模态框消失（最多等待5秒）
                    WebDriverWait(driver, 5).until(
                        EC.invisibility_of_element_located((By.CSS_SELECTOR, '.ant-modal-wrap'))
                    )
                except TimeoutException:
                    # 如果模态框未消失，尝试点击关闭按钮
                    try:
                        close_btn = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, '.ant-modal-close'))
                        )
                        close_btn.click()
                        time.sleep(1)
                    except:
                        pass  # 无模态框时忽略

            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((by, selector))
            )
            # 尝试正常点击，失败则用JS点击
            try:
                element.click()
            except:
                driver.execute_script("arguments[0].click();", element)

            if name:
                print(f"点击了 {name}")
            time.sleep(1)  # 点击后等待

        def input_element(selector, by=By.CSS_SELECTOR, value="", name=None, check_modal=True):
            # 检查并关闭可能存在的模态框
            if check_modal:
                try:
                    WebDriverWait(driver, timeout=5).until(
                        EC.invisibility_of_element_located((By.CSS_SELECTOR, '.ant-modal-wrap'))
                    )
                except TimeoutException:
                    try:
                        close_btn = WebDriverWait(driver, timeout=3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, '.ant-modal-close'))
                        )
                        close_btn.click()
                        time.sleep(1)
                    except:
                        pass  # 无模态框时忽略

            # 定位目标元素
            element = WebDriverWait(driver, timeout=10).until(
                EC.presence_of_element_located((by, selector))
            )

            # 尝试输入
            try:
                # element.clear()  # 清空输入框，若需要
                element.send_keys(value)
            except Exception as e:
                # 如果 send_keys 失败，尝试使用 JS 赋值
                try:
                    driver.execute_script("arguments[0].value = arguments[1];", element, value)
                except Exception as js_e:
                    print(f"输入失败: {e}, JS 尝试也失败: {js_e}")

            if name:
                print(f"已输入 {value} 到 {name}")

            time.sleep(1)  # 输入后等待

        def input_element_by_label_title(label_title, value="", name=None, check_modal=True):
            # 根据 label 的 title 属性定位相邻输入框并输入 value
            if check_modal:
                try:
                    WebDriverWait(driver, timeout=5).until(
                        EC.invisibility_of_element_located((By.CSS_SELECTOR, '.ant-modal-wrap'))
                    )
                except TimeoutException:
                    try:
                        close_btn = WebDriverWait(driver, timeout=3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, '.ant-modal-close'))
                        )
                        close_btn.click()
                        time.sleep(1)
                    except:
                        pass

            try:
                # XPath: 定位label ➔ 找到父div ➔ 找后面的div ➔ 找input
                # xpath = f"//label[@title='{label_title}']/parent::div/following-sibling::div//input"
                xpath = f"//label[@title='参数类型分类名称']/parent::div/following-sibling::div//input"
                # $x("//label[@title='参数类型分类名称']/parent::div/following-sibling::div//input")

                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )

                element.clear()
                element.send_keys(value)

                if name:
                    print(f"已输入 {value} 到 {name}")
                else:
                    print(f"已输入 {value} 到 label.title='{label_title}' 的输入框")

            except Exception as e:
                print(f"输入失败: {e}")

            time.sleep(1)

        time.sleep(2)

        # 原有操作
        click_element('//*[@id="headerContainer"]/div[2]/div/div[4]/a', By.XPATH, "自动推演")
        time.sleep(5)

        # 点击"开始自动推演"按钮
        click_element(
            "//*[contains(text(), '开始自动推演') and contains(@class, 'runBtnText')]",
            By.XPATH,
            "开始自动推演按钮"
        )
        time.sleep(1)

        click_element(
            '// *[ @ id = "root"] / div / div[2] / div / div[1] / div[3] / div / div[2] / div[4] / div[1] / div[1]',
            By.XPATH,
            "终止自动推演"
        )
        time.sleep(1)

        print("所有后续操作执行完毕！")
        print("请按ESC键关闭浏览器...")
        keyboard.wait('esc')  # 等待ESC键按下
        return True
    except Exception as e:
        print(f"执行后续操作时出错: {e}")
        print("请按ESC键关闭浏览器...")
        keyboard.wait('esc')  # 出错时也等待ESC键
        return False


def run_automation():
    # 执行完整的自动化流程（单个浏览器实例）
    host = '172.18.75.33'
    port = 8001

    if not check_server_connection(host, port, CONNECTION_TIMEOUT):
        return False

    driver = initialize_driver()
    try:
        if login(driver):
            return perform_post_login_actions(driver)
        return False
    finally:
        print("收到ESC键，准备关闭浏览器...")
        time.sleep(1)
        driver.quit()


def main():
    print("开始执行网页自动化脚本...")

    # 使用线程池执行（当前只运行1个实例）
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(run_automation) for _ in range(1)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]

    success_count = sum(results)
    print(f"脚本执行完毕，成功 {success_count} 次，失败 {len(results) - success_count} 次")


if __name__ == "__main__":
    main()