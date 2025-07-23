from LicenseAgent import LicenseAgent
import sys
from datetime import date, datetime, time as ti, timedelta
import multiprocessing

if __name__ == "__main__":
    try:
        Bot = LicenseAgent()
        url = "https://www.mvdis.gov.tw/m3-emv-trn/exm/locations#anchor&gsc.tab=0"
        triggerDatetime = datetime.combine(date.today()+timedelta(days=1), ti(hour=00, minute=00, second=00))
        multiprocessing.freeze_support() 

        while True:
            task = input("請輸入工作項目\nA:修改資料\nB:單視窗執行\nC:雙視窗執行\n>") 
            if task == "A":
                Bot.editConfig()
            elif task == "B":
                ack = Bot.launch(url, 10, triggerDatetime)
                while not ack:
                    Bot.launch(url, 10, triggerDatetime)
            elif task == "C":
                Bot.mutihead_launch(url, triggerDatetime)
            else:
                sys.exit()
    except Exception as e:
        print(e)
        input()