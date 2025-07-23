from datetime import date, timedelta, datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
import time, os, json, re, sys
import multiprocessing


class LicenseAgent():
    def __init__(self):
        self.configFilePath = "./res/config.json"
        self.TypeOfTest = {
            "普通重型機車":"3",
            "普通輕型機車 (50cc 以下)":"5",
            "普通小型車":"A",
            "職業小型車":"B",
            "普通大貨車":"C",
            "職業大貨車":"D",
            "普通大客車":"E",
            "職業大客車":"F",
            "普通聯結車":"G",
            "職業聯結車":"H"
        }

        self.TypeOfTest_reversed = {value: key for key, value in self.TypeOfTest.items()}


        self.configTemplate = ["考試項目(請根據上方對應填入代號)", 
                           "上下午場(上午輸入1下午輸入2)", 
                           "組別", 
                           "考場", 
                           "身分證字號", 
                           "生日(民國年)\n例如:0961231", 
                           "姓名", 
                           "電話號碼", 
                           "電子信箱"]
        self.configDict = {
            "TestDate":"",
            "licenseType":"",
            "secId":"",
            "divId":"",
            "dmvNo":"",
            "ID":"",
            "birthday":"",
            "name":"",
            "phone_number":"",
            "email":""
        }


        self.setup()


    def get_license_type_from_code(self, code):
        """
        Given a license code (e.g., "3"), returns the corresponding license type string.
        """
        return self.TypeOfTest_reversed.get(code) # Using .get() to avoid KeyError


    def readDmvlinkedLocations(self):
        path = "dmv_linked_locations_data_mapped.json"
        if getattr(sys, 'frozen', False):
            path = os.path.join(sys._MEIPASS, path)
        else:
            path = os.path.join(os.path.dirname(__file__), "res", path)

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
        
    def is_valid_email(self, email):

        """Check if the email is a valid format."""
        regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$'
        if re.match(regex, email):
            return True
        else:
            return False
        
    def print_swiftpass_banner(self):
        # (將上面的 print_swiftpass_banner 函數完整複製到這裡，或者從一個 helper 檔案導入)
        S = [" ... ", ".    ", " ... ", "    .", ".... "]
        W = [".   .", ".   .", ".   .", ". . .", " . . "]
        I = [".....", "  .  ", "  .  ", "  .  ", "....."]
        F = [".....", ".    ", "...  ", ".    ", ".    "]
        T = [".....", "  .  ", "  .  ", "  .  ", "  .  "]
        P = [".... ", ".   .", ".... ", ".    ", ".    "]
        A = [" ... ", ".   .", ".....", ".   .", ".   ."]
        blank_space = ["     ", "     ", "     ", "     ", "     "]
        word_art = [S, W, I, F, T, blank_space, P, A, S, S]
        print()
        for i in range(len(S)):
            line = []
            for letter in word_art:
                line.append(letter[i].replace(".", "/"))
            print(" ".join(line))
        print()




    def setup(self):
        self.testLocDict = self.readDmvlinkedLocations()
        self.testLocDict_reversed = {value: key for key, value in self.testLocDict.items()}
        self.print_swiftpass_banner()

        if not os.path.exists(self.configFilePath):
            print("===========尚未設定基本資料，開始設設定階段===========")
            self.configuration()
            try:
                with open(self.configFilePath, 'w', encoding="utf-8") as json_file:
                    json.dump(self.configDict, json_file, indent=4)
                
                print(f"===========✅成功寫入{self.configFilePath}===========")
                print(f"🔴請檢查輸入是否正確，若有誤可輸入A進行修改:\n路徑:{os.path.abspath(self.configFilePath)}")
                for i, t in enumerate(self.configDict):
                    match i:
                        case 0:
                            continue
                        case _:
                            print(f"- {self.configTemplate[i-1]}: {self.configDict[t]}")
        

            except IOError as e:
                print(f"Error writing to file: {e}")
            except TypeError as e:
                print(f"Error serializing data: {e}. Ensure all data types are JSON serializable.")
        else:
            with open(self.configFilePath, "r", encoding="utf-8") as f:
                self.configDict = json.load(f)

        self.form1_1 = self._get_form1_1_html()
        if self.form1_1 == None:
            raise Exception("form1_1.html not found.")

        self.form1_2 = self._get_form1_2_html()
        if self.form1_2 == None:
            raise Exception("form1_2.html not found.")     
        


    def configuration(self):
        for i, item in enumerate(self.configTemplate):
            match i:
                case 0:
                    for t in self.TypeOfTest:
                        print(f"{t}:{self.TypeOfTest[t]}")
                    info = input(f"{item}>")
                    while info not in self.TypeOfTest.values():
                        print("輸入值不在範圍內")
                        info = input(f"{item}>")
                    self.configDict["licenseType"] = info
                case 1:
                    info = input(f"{item}>")                         
                    while info != "1" and info != "2":
                        print("輸入值不在範圍內")
                        info = input(f"{item}>")
                    self.configDict["secId"] = info
                case 2:
                    info = input(f"{item}>")
                    while not info.isdigit():
                        print("輸入值不在範圍內")
                        info = input(f"{item}>")
                    self.configDict["divId"] = info
                case 3:
                    info = input(f"{item}>")
                    while info not in self.testLocDict.values():
                        print("輸入值不在範圍內")
                        info = input(f"{item}>")
                    self.configDict["dmvNo"] = info
                case 4:
                    info = input(f"{item}>")
                    while len(info) != 10:
                        print("身分證字號字數不符，請重新輸入")
                        info = input(f"{item}>")
                    self.configDict["ID"] = info
                case 5:
                    info = input(f"{item}>")
                    while (not info.isdigit()) or (int(info[:3]) > date.today().year) or not (int(info[3:5]) >= 1 and int(info[3:5]) <= 12):
                        print("輸入有誤\n注意!請使用民國年")
                        info = input(f"{item}>")
                    self.configDict["birthday"] = info
                case 6:
                    info = input(f"{item}>")
                    self.configDict["name"] = info
                case 7:
                    info = input(f"{item}>")
                    self.configDict["phone_number"] = info
                case 8:
                    info = input(f"{item}>")
                    while not self.is_valid_email(info):
                        print("請輸入正確格式的電子信箱")
                        info = input(f"{item}>")
                    self.configDict["email"] = info



        with open(self.configFilePath, 'w', encoding="utf-8") as json_file:
            json.dump(self.configDict, json_file, indent=4)
                
        print(f"===========✅成功寫入{self.configFilePath}===========")

    def editConfig(self):
        for i, item in enumerate(self.configDict):
            if i == 0:
                continue
            print(f"{i}) {self.configTemplate[i-1]}:{self.configDict[item]}")
        choice = input("請輸入您要修改的代號，以空格分開不同代號>")
        for c in re.findall(r"\d+", choice):
            c = int(c)
            match c-1:
                case 0:
                    for t in self.TypeOfTest:
                        print(f"{t}:{self.TypeOfTest[t]}")
                    info = input(f"{self.configTemplate[c-1]}>")
                    while info not in self.TypeOfTest.values():
                        print("輸入值不在範圍內")
                        info = input(f"{self.configTemplate[c-1]}>")
                    self.configDict["licenseType"] = info
                case 1:
                    info = input(f"{self.configTemplate[c-1]}>")                         
                    while info != "1" and info != "2":
                        print("輸入值不在範圍內")
                        info = input(f"{self.configTemplate[c-1]}>")
                    self.configDict["secId"] = info
                case 2:
                    info = input(f"{self.configTemplate[c-1]}>")
                    while not info.isdigit():
                        print("輸入值不在範圍內")
                        info = input(f"{self.configTemplate[c-1]}>")
                    self.configDict["divId"] = info
                case 3:
                    info = input(f"{self.configTemplate[c-1]}>")
                    while info not in self.testLocDict.values():
                        print("輸入值不在範圍內")
                        info = input(f"{self.configTemplate[c-1]}>")
                    self.configDict["dmvNo"] = info
                case 4:
                    info = input(f"{self.configTemplate[c-1]}>")
                    while len(info) != 10:
                        print("身分證字號字數不符，請重新輸入")
                        info = input(f"{self.configTemplate[c-1]}>")
                    self.configDict["ID"] = info
                case 5:
                    info = input(f"{self.configTemplate[c-1]}>")
                    while (not info.isdigit()) or (int(info[:3]) > date.today().year) or not (int(info[3:5]) >= 1 and int(info[3:5]) <= 12):
                        print("輸入有誤\n注意!請使用民國年")
                        info = input(f"{self.configTemplate[c-1]}>")
                    self.configDict["birthday"] = info
                case 6:
                    info = input(f"{self.configTemplate[c-1]}>")
                    self.configDict["name"] = info
                case 7:
                    info = input(f"{self.configTemplate[c-1]}>")
                    self.configDict["phone_number"] = info
                case 8:
                    info = input(f"{self.configTemplate[c-1]}>")
                    while not self.is_valid_email(info):
                        print("請輸入正確格式的電子信箱")
                        info = input(f"{self.configTemplate[c-1]}>")
                    self.configDict["email"] = info
        
    def get_loc_from_code(self, code):
        return self.testLocDict_reversed.get(code)

    def _load_html_template(self, template_name):
        """
        從 templates 資料夾加載 HTML 模板文件。
        """
        # 獲取當前腳本的目錄
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if getattr(sys, 'frozen', False):
            template_path = os.path.join(base_dir, sys._MEIPASS, f"{template_name}.html")
        else:
            template_path = os.path.join(base_dir, "templates", f"{template_name}.html")
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"錯誤: 模板文件 '{template_path}' 未找到。")
            return None
        except Exception as e:
            print(f"讀取模板文件時發生錯誤: {e}")
            return None

    def _get_form1_1_html(self):
        template = self._load_html_template("form1_1")
        if not template:
            return None
        
        # 使用 format() 方法填充動態數據
        # 確保字典鍵名與模板中的佔位符名稱一致
        return template.format(
            test_date=self.getTestDate(),
            sec_id=self.configDict["secId"],
            div_id=self.configDict["divId"],
            license_type_code=self.configDict["licenseType"],
            license_type_name=self.get_license_type_from_code(self.configDict["licenseType"]),
            dmv_no_code=self.configDict["dmvNo"],
            dmv_no_name=self.get_loc_from_code(self.configDict["dmvNo"])
        )
    def _get_form1_2_html(self):
        template = self._load_html_template("form1_2")
        if not template:
            return None
        
        return template.format(
            test_date=self.getTestDate(),
            sec_id=self.configDict["secId"],
            div_id=self.configDict["divId"],
            dmv_no_code=self.configDict["dmvNo"],
            license_type_code=self.configDict["licenseType"],
            id_no=self.configDict["ID"],
            birthday=self.configDict["birthday"],
            name=self.configDict["name"],
            phone_number=self.configDict["phone_number"],
            email=self.configDict["email"]
        )


    def mapTest(self, type):
        return self.TypeOfTest[type]


    def getTestDate(self):
        today = date.today()
        testDay = (today + timedelta(days=31)).strftime("%Y-%m-%d")
        return  testDay



    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option("detach", True)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        #options.add_argument(argument='--headless')  # 無頭模式，不顯示瀏覽器界面

        # --- IMPORTANT: Specify ChromeDriver path explicitly ---
        if getattr(sys, 'frozen', False): # Check if running as a PyInstaller frozen executable
            # For PyInstaller: ChromeDriver is expected to be in the temporary _MEIPASS folder
            # On Windows: chromedriver.exe
            # On macOS/Linux: chromedriver (no .exe)
            driver_executable_name = "chromedriver.exe" if sys.platform.startswith('win') else "chromedriver"
            driver_path = os.path.join(sys._MEIPASS, driver_executable_name)

            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=options)

            
        else:
            driver = webdriver.Chrome(options=options)
        return driver
        




    def precise_delay(self, target_datetime_obj, offset_ms, process_name=False):
        """
        計算與目標時間的時間間隔，並延遲該間隔，以毫秒或微秒為基礎進行計算。
        在遠離目標時間時使用 time.sleep 讓出 CPU，
        在接近目標時間時使用忙碌等待以提高精確度。

        Args:
            target_datetime_obj (datetime): 期望報名成功 (伺服器端確認) 的目標時間點。
        """
        
        # 1. 計算實際要開始發送請求的「觸發」時間點
        # 這是你的程式應該開始執行 driver.execute_script 的時間
        trigger_time_for_execution = target_datetime_obj - timedelta(milliseconds=offset_ms)
        if process_name:
            print(f"[{process_name}] 期望報名成功時間: {target_datetime_obj}")
            print(f"[{process_name}] 實際觸發請求時間點: {trigger_time_for_execution}")
        else:
            print(f"期望報名成功時間: {target_datetime_obj}")
            print(f"實際觸發請求時間點: {trigger_time_for_execution}")
        # 將 trigger_time_for_execution 轉換為 perf_counter_ns 的對應值
        # 這樣可以利用 time.perf_counter_ns() 的高精度特性
        # current_perf_counter_ns_now = time.perf_counter_ns()
        # current_system_time_ns_now = datetime.now().timestamp() * 1_000_000_000
        # trigger_time_actual_ns_system_time = trigger_time_for_execution.timestamp() * 1_000_000_000
        
        # 確保基準點一致，避免 datetime.now() 的浮點數誤差和系統時鐘跳變
        # 計算相對於當前 perf_counter_ns 的目標點
        trigger_perf_counter_ns_target = time.perf_counter_ns() + (trigger_time_for_execution.timestamp() * 1_000_000_000 - datetime.now().timestamp() * 1_000_000_000)

        # 設定一個閾值，在這個閾值之外使用 time.sleep
        # 進入這個閾值內，就切換到忙碌等待
        # 這個值通常設定為數百毫秒，例如 200毫秒 (0.2秒)
        SLEEP_THRESHOLD_NS = 200 * 1_000_000 # 200 毫秒 (轉換為納秒)
        
        while True:
            current_perf_counter_ns = time.perf_counter_ns()
            remaining_ns = trigger_perf_counter_ns_target - current_perf_counter_ns
            
            # 如果已經過了觸發時間點，立即退出迴圈
            if remaining_ns <= 0:
                return # 函式結束
            
            # 如果剩餘時間較長，使用 time.sleep 讓出 CPU
            if remaining_ns > SLEEP_THRESHOLD_NS:
                # 將納秒轉換為秒 (time.sleep 接受秒數)
                sleep_seconds = remaining_ns / 1_000_000_000 
                time.sleep(sleep_seconds)
            else:
                # 進入最後的忙碌等待階段，直到精確時間點
                # 在這裡不會再調用 time.sleep，而是持續檢查時間
                pass # 這就是忙碌等待，CPU 使用率會高，但精確

    def launch(self, url, offset_ms, triggerDatetime):
        print("=====啟動資料確認=====")
        print(f"現在時刻:{datetime.now()}\n📅考試日期:{self.configDict['TestDate']}\n預計觸發時間:{triggerDatetime}")
        for i, t in enumerate(self.configDict):
            match i:
                case 0:
                    continue
                case _:
                    print(f"- {self.configTemplate[i-1]}: {self.configDict[t]}")
        try:
            print("=====啟動程序=====")
            driver = self.setup_driver()
            print(f"Navigating to {url}...")
            driver.get(url)
            # 等待 form1 元素出現
            try:
                # 等待 body 元素出現 (基本頁面加載完成)
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                print("頁面 body 已加載。")

                # 等待 jQuery 加載完成。這裡會執行一個 JavaScript 檢查，判斷 window.jQuery 是否存在。
                # 這是最直接判斷 jQuery 是否就緒的方法。
                WebDriverWait(driver, 5).until(
                    lambda d: d.execute_script("return typeof jQuery != 'undefined' && jQuery.active == 0")
                )
                print("jQuery 已加載且沒有活躍的 AJAX 請求。")

                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "form1"))
                )

            except TimeoutException:
                print("警告: 頁面加載或 jQuery 加載超時。正在重新啟動")
                return False
            # 使用 JavaScript 來移除舊的 form1 並插入新的 HTML
            # 我們會找到 form1 的父元素，然後用新的 HTML 替換舊的 form1



            script = f"""
            var oldForm = document.getElementById('form1');
            if (oldForm) {{
                // 直接將新 HTML 字串賦值給舊元素的 outerHTML
                oldForm.outerHTML = `{self.form1_1}`;
                console.log("Form1 replaced using outerHTML!");
            }}
            """


            driver.execute_script(script)
            print("Attempted to replace form1 with custom HTML.")



            submit_form1_js = '''
                $('#form1').submit();
            '''
            try:
                self.precise_delay(triggerDatetime, offset_ms)
                start = time.perf_counter_ns()
                driver.execute_script(submit_form1_js)
                end = time.perf_counter_ns()
                span = (end - start) / 1_000_000_000
                print(f"time span:{span:.3f}")
                try:
                    # 等待 jQuery 加載完成。這裡會執行一個 JavaScript 檢查，判斷 window.jQuery 是否存在。
                    # 這是最直接判斷 jQuery 是否就緒的方法。
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.ID, "form1"))
                    )
                except TimeoutException:
                    print("警告: 頁面加載超時。請手動輸入")
                else:


                    script = f"""
                    var oldForm = document.getElementById('form1');
                    if (oldForm) {{
                        // 直接將新 HTML 字串賦值給舊元素的 outerHTML
                        oldForm.outerHTML = `{self.form1_2}`;
                        console.log("Form1 replaced using outerHTML!");
                    }}
                    """
                    driver.execute_script(script)
                    print("Attempted to replace form1 with custom HTML.")
                    driver.execute_script(submit_form1_js)
                    return True
            except Exception as e:
                print(f"Not Working!!{e}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            input("程式結束，按下enter結束畫面>")
            driver.quit()
            print("Browser closed.")


    def launch_for_mutihead(self, url, process_name, offset_ms, triggerDatetime):
        print(f"=====啟動{process_name}=====")
        try:
            driver = self.setup_driver()
            driver.get(url)
            # 等待 form1 元素出現
            try:
                # 等待 body 元素出現 (基本頁面加載完成)
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                print(f"[{process_name}] 頁面 body 已加載。")

                # 等待 jQuery 加載完成。這裡會執行一個 JavaScript 檢查，判斷 window.jQuery 是否存在。
                # 這是最直接判斷 jQuery 是否就緒的方法。
                WebDriverWait(driver, 5).until(
                    lambda d: d.execute_script("return typeof jQuery != 'undefined' && jQuery.active == 0")
                )
                print(f"[{process_name}] jQuery 已加載且沒有活躍的 AJAX 請求。")

                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "form1"))
                )

            except TimeoutException:
                print(f"[{process_name}] 警告: 頁面加載或 jQuery 加載超時。正在重新啟動")
                return False
            # 使用 JavaScript 來移除舊的 form1 並插入新的 HTML
            # 我們會找到 form1 的父元素，然後用新的 HTML 替換舊的 form1



            script = f"""
            var oldForm = document.getElementById('form1');
            if (oldForm) {{
                // 直接將新 HTML 字串賦值給舊元素的 outerHTML
                oldForm.outerHTML = `{self.form1_1}`;
                console.log("Form1 replaced using outerHTML!");
            }}
            """


            driver.execute_script(script)
            print(f"[{process_name}] Attempted to replace form1 with custom HTML.")



            submit_form1_js = '''
                $('#form1').submit();
            '''
            try:
                self.precise_delay(triggerDatetime, offset_ms, process_name)
                start = time.perf_counter_ns()
                driver.execute_script(submit_form1_js)
                end = time.perf_counter_ns()
                span = (end - start) / 1_000_000_000
                print(f"[{process_name}] time span:{span:.3f}")
                try:
                    # 等待 jQuery 加載完成。這裡會執行一個 JavaScript 檢查，判斷 window.jQuery 是否存在。
                    # 這是最直接判斷 jQuery 是否就緒的方法。
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.ID, "form1"))
                    )
                except TimeoutException:
                    print(f"[{process_name}] 警告: 頁面加載超時。請手動輸入")
                else:


                    script = f"""
                    var oldForm = document.getElementById('form1');
                    if (oldForm) {{
                        // 直接將新 HTML 字串賦值給舊元素的 outerHTML
                        oldForm.outerHTML = `{self.form1_2}`;
                        console.log("Form1 replaced using outerHTML!");
                    }}
                    """
                    driver.execute_script(script)
                    print(f"[{process_name}] Attempted to replace form1 with custom HTML.")
                    driver.execute_script(submit_form1_js)
                    return True
            except Exception as e:
                print(f"Not Working!!{e}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            input("程式結束，按下enter結束畫面>")
            driver.quit()
            print("Browser closed.")





    def mutihead_launch(self, url, triggerDatetime):
        print("=====啟動資料確認=====")
        print(f"現在時刻:{datetime.now()}\n📅考試日期:{self.getTestDate()}\n預計觸發時間:{triggerDatetime}")
        for i, t in enumerate(self.configDict):
            match i:
                case 0:
                    continue
                case _:
                    print(f"- {self.configTemplate[i-1]}: {self.configDict[t]}")
        print("====================")

        trigger_offsets = [10, -10]
        processes = []
        for offset in trigger_offsets:
            process_name = f"DriverProcess:{offset}"
            p = multiprocessing.Process(target=self.launch_for_mutihead, name=process_name, args=(url, process_name, offset, triggerDatetime))
            processes.append(p)
            p.start()
        
        for p in processes:
            p.join()

        print("所有嘗試進程已完成")