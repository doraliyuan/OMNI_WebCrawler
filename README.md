# OMNI_WebCrawler
Download data from NASA GSFC (Goddard Space Flight Center) SPDC (Space Physics Data Facility) OMNIWeb

# 程式目的
於NASA OMNIWeb網站下載所需新資料，並計算所需參數，最後合併過去資料的檔案(NetCDF)。

# 緣起
為了跑電離層TIEGCM模式。

# 執行程式之前需要
1. 資料夾要有合併的舊檔案，gpi_1960001-2020366.nc。
2. 在程式第33行的地方，可以更改最新資料的日期，舉例來說，當參數設為 end_year = 2023, end_doy = 207，會產生減40天檔名的nc檔，gpi_1960001-2023167.nc。
3. 個人環境中安裝所需的python套件。

# 如何使用
`python fetch_omni_data.py`
