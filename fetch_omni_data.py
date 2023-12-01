'''
Download data from NASA OMNIWeb
Usage: python fetch_omni_data.py [start_year] [start_doy] [end_year] [end_doy] 
Author      : Wang, Li-Yuan
Since       : 2023/08/08
Update notes:
'''

# 需要的套件，沒有請安裝
import requests
import netCDF4 as nc
import numpy as np
from bs4 import BeautifulSoup
from warnings import filterwarnings
filterwarnings(action='ignore', category=DeprecationWarning, message='`np.bool` is a deprecated alias')
import sys, os

'''
#吃外部變數
try:
    start_year = int(sys.argv[1]) 
    start_doy  = int(sys.argv[2]) 
    end_year   = int(sys.argv[3]) 
    end_doy    = int(sys.argv[4]) 
except IndexError:
    print('Usage: python download_cwb_gdms_data.py [start_year] [start_doy] [end_year] [end_doy]')
    sys.exit()
'''

# 手動設定參數
start_year = 2021
start_doy  = 1
end_year   = 2023
end_doy    = 207         #請大於等於2021041，否則會有錯誤

sd = '%03d' % start_doy
ed = '%03d' % end_doy
t1 = str(start_year)+sd 
t2 = str(end_year)+ed
print('start date: '+t1)
print('end date: '+t2)

# 欲下載的資料，1:Kp 2:F10.7
search_data1 = {'activity':'retrieve','res':'hour','spacecraft':'omni2','start_date':t1,'end_date':t2,'vars':'38'}
search_data2 = {'activity':'retrieve','res':'daily','spacecraft':'omni2_daily','start_date':t1,'end_date':t2,'vars':'50'}

# 偽裝成瀏覽器
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.35'}

# 送出表單資料
res1 = requests.post('https://omniweb.gsfc.nasa.gov/cgi/nx1.cgi', data=search_data1, headers=headers)
res2 = requests.post('https://omniweb.gsfc.nasa.gov/cgi/nx1.cgi', data=search_data2, headers=headers)

# 表單回傳結果
soup1 = BeautifulSoup(res1.text, "html.parser")
result1 = str(soup1.find("pre"))
soup2 = BeautifulSoup(res2.text, "html.parser")
result2 = str(soup2.find("pre"))

# 字串處理-以分行符號分隔
lines1 = result1.splitlines()
lines2 = result2.splitlines()

# 自動判斷索取的參數有幾個
n1 = lines1.index('')
print('There are total '+str(n1-1)+' parameters.')
n2 = lines2.index('')
print('There are total '+str(n2-1)+' parameters.')

# 自動判斷索取的參數名稱
pars_tmp1 = lines1[1:n1]
pars1 = [x[3:] for x in pars_tmp1]
print('The parameters are: '+str(pars1))
pars_tmp2 = lines2[1:n2]
pars2 = [x[3:] for x in pars_tmp2]
print('The parameters are: '+str(pars2))

# 實際想要的資料(不包含head與欄位名稱)
data1 = lines1[n1+2:len(lines1)-1]
year1 = [x.split()[0] for x in data1]
doy1 = [x.split()[1] for x in data1]
hour1 = [x.split()[2] for x in data1]
kp1 = [x.split()[3] for x in data1]

data2 = lines2[n2+2:len(lines2)-1]
year2 = [x.split()[0] for x in data2]
doy2 = [x.split()[1] for x in data2]
hour2 = [x.split()[2] for x in data2]
f107 = [x.split()[3] for x in data2]

#************* 爬蟲部分到這邊 *************

# 讀取NetCDF檔、'numpy.ma.core.MaskedArray'轉list字串
rootgrp = nc.Dataset("gpi_1960001-2020366.nc") 
#rootgrp # show metadata information
year_day = rootgrp.variables['year_day'][:].tolist()
f107d = rootgrp.variables['f107d'][:].tolist()
f107a = rootgrp.variables['f107a'][:].tolist()
kp = rootgrp.variables['kp'][:].tolist()

# 只要其參數之時間範圍為1960~2020的部分
t = year_day.index(2020366)
f107d_2020 = f107d[0:t+1]
f107a_2020 = f107a[0:t+1]
kp_2020 = kp[0:t+1][:]

# 計算每3小時的kp(網站的kp)
kp_3hr_tmp = kp1[0:len(kp1):3]
kp_3hr = [float(x) for x in kp_3hr_tmp] #先把字串轉為浮點數
kp_3hr_2d = np.array(kp_3hr).reshape(-1, 8).tolist() #再把矩陣轉為2D形式

# 合併檔案的資料與爬蟲的資料
f107d_mix_tmp = f107d_2020+f107
f107d_mix = [float(x) for x in f107d_mix_tmp] #為了把爬蟲資料的字串轉浮點數
kp_mix = kp_2020+kp_3hr_2d

# 計算F10.7的running mean
N = 81
f107a_yuan_tmp = np.convolve(f107d_mix, np.ones(N)/N, mode='valid')
f107a_yuan = f107a_yuan_tmp.tolist()
s = (N-1)/2
f107a_mix = f107a_2020+f107a_yuan[t+1-int(s):] #原本檔案的F10.7a之1960001~20201231，與自己計算的F10.7a之2021001後的資料

## 比較兩者的F10.7a
#s = (N-1)/2
#t1 = year_day.index(2021001)
#t2 = year_day.index(2021019)
#print(f107a_new[t1-int(s):t2+1-int(s)]) #自己計算的2021.01.01~2021.01.19，注意:資料總數會少80個
#print(f107a[len(f107a)-19:len(f107a)]) #原本檔案的2021.01.01~2021.01.19

# 輸出成NetCDF檔
fo_start_year = 1960
fo_end_doy = int(end_doy-((N-1)/2))
if fo_end_doy <=0:
    fo_end_year = end_year-1
    edoy = 366 if (fo_end_year % 4 == 0 and fo_end_year % 100 != 0) or (fo_end_year % 400 == 0) else 365
    fo_end_doy = fo_end_doy+edoy
else:
    fo_end_year = end_year

fo_end_doy_s = '%03d' % fo_end_doy
print(str(fo_end_year)+fo_end_doy_s)

yyyyddd = []
for year in range(fo_start_year, fo_end_year + 1):
    days_in_year = 366 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 365
    max_doy = days_in_year if year < fo_end_year else fo_end_doy    
    for doy in range(1, max_doy + 1):
        yyyyddd.append(year * 1000 + doy)

new_file_path = 'gpi_1960001-'+str(fo_end_year)+fo_end_doy_s+'.nc'
if os.path.exists(new_file_path):
    os.remove(new_file_path)

with nc.Dataset(new_file_path, 'w', format='NETCDF4') as new_dataset:    

    new_dataset.title = 'Geophysical Indices, obtained from NGDC(1960~2020) and NASA OMNI(2021001~)'
    new_dataset.yearday_beg = '1960001'
    new_dataset.yearday_end = str(fo_end_year)+fo_end_doy_s
    data_source_url_1 = 'ftp://ftp.ngdc.noaa.gov/STP/GEOMAGNETIC_DATA/INDICES/KP_AP/'
    data_source_url_2 = 'https://omniweb.gsfc.nasa.gov/form/dx1.html'
            
    new_dataset.createDimension('ndays', len(yyyyddd))
    new_dataset.createDimension('nkp', 8)

    year_day_var = new_dataset.createVariable('year_day', 'f4', ('ndays',))
    f107d_var = new_dataset.createVariable('f107d', 'f8', ('ndays',))
    f107a_var = new_dataset.createVariable('f107a', 'f8', ('ndays',))
    kp_var = new_dataset.createVariable('kp', 'f8', ('ndays', 'nkp'))

    year_day_var[:] = yyyyddd
    f107d_var[:] = f107d_mix[0:len(f107d_mix)-int(s)] #只需要到2023167
    f107a_var[:] = f107a_mix
    kp_var[:] = kp_mix[0:len(kp_mix)-int(s)][:] #只需要到2023167
    
    year_day_var.long_name = '4-digit year followed by 3-digit day'
    f107d_var.long_name = 'daily 10.7 cm solar flux'
    f107a_var.long_name = '81-day average 10.7 cm solar flux'
    kp_var.long_name = '3-hourly kp index'