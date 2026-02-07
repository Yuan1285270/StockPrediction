import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

import yfinance as yf
import pandas as pd

# ========= 500 檔台股清單 (上市股票) =========
SYMBOLS = [
    "1101.TW",  # 台泥
    "1102.TW",  # 亞泥
    "1103.TW",  # 嘉泥
    "1104.TW",  # 環泥
    "1108.TW",  # 幸福
    "1109.TW",  # 信大
    "1110.TW",  # 東泥
    "1201.TW",  # 味全
    "1203.TW",  # 味王
    "1210.TW",  # 大成
    "1213.TW",  # 大飲
    "1215.TW",  # 卜蜂
    "1216.TW",  # 統一
    "1217.TW",  # 愛之味
    "1218.TW",  # 泰山
    "1219.TW",  # 福壽
    "1220.TW",  # 台榮
    "1225.TW",  # 福懋油
    "1227.TW",  # 佳格
    "1229.TW",  # 聯華
    "1231.TW",  # 聯華食
    "1232.TW",  # 大統益
    "1233.TW",  # 天仁
    "1234.TW",  # 黑松
    "1235.TW",  # 興泰
    "1236.TW",  # 宏亞
    "1256.TW",  # 鮮活果汁-KY
    "1301.TW",  # 台塑
    "1303.TW",  # 南亞
    "1304.TW",  # 台聚
    "1305.TW",  # 華夏
    "1307.TW",  # 三芳
    "1308.TW",  # 亞聚
    "1309.TW",  # 台達化
    "1310.TW",  # 台苯
    "1312.TW",  # 國喬
    "1313.TW",  # 聯成
    "1314.TW",  # 中石化
    "1315.TW",  # 達新
    "1316.TW",  # 上曜
    "1319.TW",  # 東陽
    "1321.TW",  # 大洋
    "1323.TW",  # 永裕
    "1324.TW",  # 地球
    "1325.TW",  # 恆大
    "1326.TW",  # 台化
    "1337.TW",  # 再生-KY
    "1338.TW",  # 廣華-KY
    "1339.TW",  # 昭輝
    "1340.TW",  # 勝悅-KY
    "1341.TW",  # 富林-KY
    "1342.TW",  # 八貫
    "1402.TW",  # 遠東新
    "1409.TW",  # 新纖
    "1410.TW",  # 南染
    "1413.TW",  # 宏洲
    "1414.TW",  # 東和
    "1416.TW",  # 廣豐
    "1417.TW",  # 嘉裕
    "1418.TW",  # 東華
    "1419.TW",  # 新紡
    "1423.TW",  # 利華
    "1432.TW",  # 大魯閣
    "1434.TW",  # 福懋
    "1435.TW",  # 中福
    "1436.TW",  # 華友聯
    "1437.TW",  # 勤益控
    "1438.TW",  # 三發地產
    "1439.TW",  # 雋揚
    "1440.TW",  # 南紡
    "1441.TW",  # 大東
    "1442.TW",  # 名軒
    "1443.TW",  # 立益
    "1444.TW",  # 力麗
    "1445.TW",  # 大宇
    "1446.TW",  # 宏和
    "1447.TW",  # 力鵬
    "1449.TW",  # 佳和
    "1451.TW",  # 本盟
    "1452.TW",  # 宏益
    "1453.TW",  # 大將
    "1454.TW",  # 台富
    "1455.TW",  # 集盛
    "1456.TW",  # 怡華
    "1457.TW",  # 宜進
    "1459.TW",  # 聯發
    "1460.TW",  # 宏遠
    "1463.TW",  # 強盛
    "1464.TW",  # 得力
    "1465.TW",  # 偉全
    "1466.TW",  # 聚隆
    "1467.TW",  # 南緯
    "1468.TW",  # 昶和
    "1470.TW",  # 大統新創
    "1471.TW",  # 首利
    "1472.TW",  # 三洋實業
    "1473.TW",  # 台南
    "1474.TW",  # 弘裕
    "1475.TW",  # 業旺
    "1476.TW",  # 聚陽
    "1477.TW",  # 聚大
    "1503.TW",  # 士電
    "1504.TW",  # 東元
    "1506.TW",  # 正道
    "1507.TW",  # 永大
    "1512.TW",  # 瑞利
    "1513.TW",  # 中興電
    "1514.TW",  # 亞力
    "1515.TW",  # 力山
    "1516.TW",  # 川飛
    "1517.TW",  # 利奇
    "1519.TW",  # 華城
    "1521.TW",  # 大經
    "1522.TW",  # 堤維西
    "1524.TW",  # 耿鼎
    "1525.TW",  # 江申
    "1526.TW",  # 日馳
    "1527.TW",  # 鑽全
    "1528.TW",  # 恩德
    "1529.TW",  # 樂士
    "1530.TW",  # 亞崴
    "1531.TW",  # 高林股
    "1532.TW",  # 勤美
    "1533.TW",  # 車王電
    "1535.TW",  # 中宇
    "1536.TW",  # 和大
    "1537.TW",  # 廣隆
    "1538.TW",  # 正峰
    "1539.TW",  # 巨庭
    "1540.TW",  # 喬福
    "1541.TW",  # 錩泰
    "1558.TW",  # 伸興
    "1560.TW",  # 中砂
    "1568.TW",  # 倉佑
    "1582.TW",  # 信錦
    "1583.TW",  # 程泰
    "1587.TW",  # 吉茂
    "1589.TW",  # 永冠-KY
    "1590.TW",  # 亞德客-KY
    "1597.TW",  # 直得
    "1598.TW",  # 岱宇
    "1603.TW",  # 華電
    "1604.TW",  # 聲寶
    "1605.TW",  # 華新
    "1608.TW",  # 華榮
    "1609.TW",  # 大亞
    "1611.TW",  # 中電
    "1612.TW",  # 宏泰
    "1614.TW",  # 三洋電
    "1615.TW",  # 大山
    "1616.TW",  # 億泰
    "1617.TW",  # 榮星
    "1618.TW",  # 合機
    "1626.TW",  # 艾美特-KY
    "1701.TW",  # 中化
    "1702.TW",  # 南僑
    "1704.TW",  # 榮化
    "1707.TW",  # 葡萄王
    "1708.TW",  # 東鹼
    "1709.TW",  # 和益
    "1710.TW",  # 東聯
    "1711.TW",  # 永光
    "1712.TW",  # 興農
    "1713.TW",  # 國化
    "1714.TW",  # 和桐
    "1717.TW",  # 長興
    "1718.TW",  # 中纖
    "1720.TW",  # 生達
    "1721.TW",  # 三晃
    "1722.TW",  # 台肥
    "1723.TW",  # 中碳
    "1724.TW",  # 台蠟
    "1725.TW",  # 元禎
    "1726.TW",  # 永記
    "1727.TW",  # 中華化
    "1730.TW",  # 花仙子
    "1731.TW",  # 美吾華
    "1732.TW",  # 毛寶
    "1733.TW",  # 五鼎
    "1734.TW",  # 杏輝
    "1735.TW",  # 日勝化
    "1736.TW",  # 喬山
    "1737.TW",  # 臺鹽
    "1760.TW",  # 寶齡富錦
    "1762.TW",  # 中化生
    "1773.TW",  # 勝一
    "1776.TW",  # 展宇
    "1783.TW",  # 和康生
    "1786.TW",  # 財團法人
    "1789.TW",  # 神隆
    "1795.TW",  # 美時
    "1802.TW",  # 台玻
    "1805.TW",  # 寶徠
    "1806.TW",  # 冠軍
    "1808.TW",  # 潤隆
    "1809.TW",  # 中釉
    "1810.TW",  # 和成
    "1817.TW",  # 凱撒衛
    "1903.TW",  # 士紙
    "1904.TW",  # 正隆
    "1905.TW",  # 華紙
    "1906.TW",  # 寶隆
    "1907.TW",  # 永豐餘
    "1909.TW",  # 榮成
    "2002.TW",  # 中鋼
    "2006.TW",  # 東鋼
    "2007.TW",  # 燁興
    "2008.TW",  # 高興昌
    "2009.TW",  # 第一銅
    "2010.TW",  # 春源
    "2012.TW",  # 春雨
    "2013.TW",  # 中鋼構
    "2014.TW",  # 中鴻
    "2015.TW",  # 豐興
    "2017.TW",  # 官田鋼
    "2020.TW",  # 美亞
    "2022.TW",  # 聚亨
    "2023.TW",  # 燁輝
    "2024.TW",  # 志聯
    "2025.TW",  # 千興
    "2027.TW",  # 大成鋼
    "2028.TW",  # 威致
    "2029.TW",  # 盛餘
    "2030.TW",  # 彰源
    "2031.TW",  # 新光鋼
    "2032.TW",  # 新鋼
    "2033.TW",  # 佳源
    "2034.TW",  # 允強
    "2038.TW",  # 海光
    "2049.TW",  # 上銀
    "2059.TW",  # 川湖
    "2062.TW",  # 橋椿
    "2101.TW",  # 南港
    "2102.TW",  # 泰豐
    "2103.TW",  # 台橡
    "2104.TW",  # 中橡
    "2105.TW",  # 正新
    "2106.TW",  # 建大
    "2107.TW",  # 厚生
    "2108.TW",  # 南帝
    "2109.TW",  # 華豐
    "2114.TW",  # 鑫永銓
    "2115.TW",  # 六暉-KY
    "2201.TW",  # 裕隆
    "2204.TW",  # 中華
    "2206.TW",  # 三陽工業
    "2207.TW",  # 和泰車
    "2208.TW",  # 台船
    "2211.TW",  # 長榮鋼
    "2227.TW",  # 裕日車
    "2228.TW",  # 劍麟
    "2231.TW",  # 為升
    "2233.TW",  # 宇隆
    "2236.TW",  # 百達-KY
    "2239.TW",  # 英利-KY
    "2243.TW",  # 宏旭-KY
    "2247.TW",  # 汎德永業
    "2301.TW",  # 光寶科
    "2302.TW",  # 麗正
    "2303.TW",  # 聯電
    "2305.TW",  # 全友
    "2308.TW",  # 台達電
    "2312.TW",  # 金寶
    "2313.TW",  # 華通
    "2314.TW",  # 台揚
    "2316.TW",  # 楠梓電
    "2317.TW",  # 鴻海
    "2321.TW",  # 東訊
    "2323.TW",  # 中環
    "2324.TW",  # 仁寶
    "2327.TW",  # 國巨
    "2328.TW",  # 廣宇
    "2329.TW",  # 華泰
    "2330.TW",  # 台積電
    "2331.TW",  # 精英
    "2332.TW",  # 友訊
    "2337.TW",  # 旺宏
    "2338.TW",  # 光罩
    "2340.TW",  # 台亞
    "2342.TW",  # 茂矽
    "2344.TW",  # 華邦電
    "2345.TW",  # 智邦
    "2347.TW",  # 聯強
    "2348.TW",  # 海悅
    "2349.TW",  # 錸德
    "2351.TW",  # 順德
    "2352.TW",  # 佳世達
    "2353.TW",  # 宏碁
    "2354.TW",  # 鴻準
    "2355.TW",  # 敬鵬
    "2356.TW",  # 英業達
    "2357.TW",  # 華碩
    "2358.TW",  # 廷鑫
    "2359.TW",  # 所羅門
    "2360.TW",  # 致茂
    "2362.TW",  # 藍天
    "2363.TW",  # 矽統
    "2364.TW",  # 倫飛
    "2365.TW",  # 昆盈
    "2367.TW",  # 燿華
    "2368.TW",  # 金像電
    "2369.TW",  # 菱生
    "2371.TW",  # 大同
    "2373.TW",  # 震旦行
    "2374.TW",  # 佳能
    "2375.TW",  # 凱美
    "2376.TW",  # 技嘉
    "2377.TW",  # 微星
    "2379.TW",  # 瑞昱
    "2380.TW",  # 虹光
    "2382.TW",  # 廣達
    "2383.TW",  # 台光電
    "2385.TW",  # 群光
    "2387.TW",  # 精元
    "2388.TW",  # 威盛
    "2390.TW",  # 云辰
    "2392.TW",  # 正崴
    "2393.TW",  # 億光
    "2395.TW",  # 研華
    "2397.TW",  # 友通
    "2399.TW",  # 映泰
    "2401.TW",  # 凌陽
    "2402.TW",  # 毅嘉
    "2404.TW",  # 漢唐
    "2405.TW",  # 輔信
    "2406.TW",  # 國碩
    "2408.TW",  # 南亞科
    "2409.TW",  # 群創
    "2412.TW",  # 中華電
    "2413.TW",  # 環科
    "2414.TW",  # 精技
    "2415.TW",  # 錩新
    "2417.TW",  # 圓剛
    "2419.TW",  # 仲琦
    "2420.TW",  # 毅金
    "2421.TW",  # 建準
    "2423.TW",  # 固緯
    "2424.TW",  # 隴華
    "2425.TW",  # 承啟
    "2426.TW",  # 鼎元
    "2427.TW",  # 三商電
    "2428.TW",  # 興勤
    "2430.TW",  # 燦坤
    "2431.TW",  # 聯昌
    "2433.TW",  # 互盛電
    "2434.TW",  # 統懋
    "2436.TW",  # 偉詮電
    "2438.TW",  # 翔耀
    "2439.TW",  # 美律
    "2440.TW",  # 太空梭
    "2441.TW",  # 超豐
    "2442.TW",  # 新美齊
    "2443.TW",  # 昶虹
    "2444.TW",  # 友勁
    "2449.TW",  # 京元電子
    "2450.TW",  # 神腦
    "2451.TW",  # 創見
    "2453.TW",  # 凌群
    "2454.TW",  # 聯發科
    "2455.TW",  # 全新
    "2456.TW",  # 奇力新
    "2457.TW",  # 飛宏
    "2458.TW",  # 義隆
    "2459.TW",  # 敦吉
    "2460.TW",  # 建通
    "2461.TW",  # 光群雷
    "2462.TW",  # 良得電
    "2464.TW",  # 盟立
    "2465.TW",  # 麗臺
    "2466.TW",  # 冠西電
    "2467.TW",  # 志聖
    "2468.TW",  # 華經
    "2471.TW",  # 資通
    "2472.TW",  # 立隆電
    "2474.TW",  # 可成
    "2475.TW",  # 華映
    "2476.TW",  # 鉅祥
    "2477.TW",  # 美隆電
    "2478.TW",  # 大毅
    "2480.TW",  # 敦陽科
    "2481.TW",  # 強茂
    "2482.TW",  # 連宇
    "2483.TW",  # 百容
    "2484.TW",  # 希華
    "2485.TW",  # 兆赫
    "2486.TW",  # 一詮
    "2488.TW",  # 漢平
    "2489.TW",  # 瑞軒
    "2491.TW",  # 吉祥全
    "2492.TW",  # 華新科
    "2493.TW",  # 揚博
    "2495.TW",  # 普安
    "2496.TW",  # 卓越
    "2497.TW",  # 怡利電
    "2498.TW",  # 宏達電
    "2501.TW",  # 國建
    "2504.TW",  # 國產
    "2505.TW",  # 國美
    "2506.TW",  # 太設
    "2509.TW",  # 全坤建
    "2511.TW",  # 太子
    "2514.TW",  # 龍邦
    "2515.TW",  # 中工
    "2516.TW",  # 新建
    "2520.TW",  # 冠德
    "2524.TW",  # 京城
    "2527.TW",  # 宏璟
    "2528.TW",  # 皇普
    "2530.TW",  # 華建
    "2534.TW",  # 宏盛
    "2535.TW",  # 達欣工
    "2536.TW",  # 宏普
    "2537.TW",  # 聯上發
    "2538.TW",  # 基泰
    "2539.TW",  # 櫻花建
    "2542.TW",  # 興富發
    "2543.TW",  # 皇昌
    "2545.TW",  # 皇翔
    "2546.TW",  # 根基
    "2547.TW",  # 日勝生
    "2548.TW",  # 華固
    "2597.TW",  # 潤弘
    "2601.TW",  # 益航
    "2603.TW",  # 長榮
    "2605.TW",  # 新興
    "2606.TW",  # 裕民
    "2607.TW",  # 榮運
    "2608.TW",  # 大榮
    "2609.TW",  # 陽明
    "2610.TW",  # 華航
    "2611.TW",  # 志信
    "2612.TW",  # 中航
    "2613.TW",  # 中櫃
    "2614.TW",  # 東森
    "2615.TW",  # 萬海
    "2616.TW",  # 山隆
    "2617.TW",  # 台航
    "2618.TW",  # 長榮航
    "2630.TW",  # 亞航
    "2633.TW",  # 台灣高鐵
    "2634.TW",  # 漢翔
    "2636.TW",  # 台驊
    "2637.TW",  # 慧洋-KY
    "2642.TW",  # 宅配通
    "2701.TW",  # 萬企
    "2702.TW",  # 華園
    "2704.TW",  # 國賓
    "2705.TW",  # 六福
    "2706.TW",  # 第一店
    "2707.TW",  # 晶華
    "2712.TW",  # 遠雄來
    "2722.TW",  # 夏都
    "2723.TW",  # 美食-KY
    "2727.TW",  # 王品
    "2731.TW",  # 雄獅
    "2739.TW",  # 寒舍
    "2748.TW",  # 汎武
    "2753.TW",  # 八方雲集
    "2801.TW",  # 彰銀
    "2809.TW",  # 京城銀
    "2812.TW",  # 台中銀
    "2816.TW",  # 旺旺保
    "2820.TW",  # 華票
    "2823.TW",  # 中壽
    "2832.TW",  # 台產
    "2834.TW",  # 臺企銀
    "2836.TW",  # 萬泰銀
    "2838.TW",  # 聯邦銀
    "2841.TW",  # 台開
    "2845.TW",  # 遠東銀
    "2849.TW",  # 安泰銀
    "2850.TW",  # 新產
    "2851.TW",  # 中再保
    "2852.TW",  # 第一保
    "2855.TW",  # 寶來證
    "2856.TW",  # 元富證
    "2867.TW",  # 三商壽
    "2880.TW",  # 華南金
    "2881.TW",  # 富邦金
    "2882.TW",  # 國泰金
    "2883.TW",  # 開發金
    "2884.TW",  # 玉山金
    "2885.TW",  # 元大金
    "2886.TW",  # 兆豐金
    "2887.TW",  # 台新金
    "2888.TW",  # 新光金
    "2889.TW",  # 國票金
    "2890.TW",  # 永豐金
    "2891.TW",  # 中信金
    "2892.TW",  # 第一金
    "2897.TW",  # 王道銀
    "2901.TW",  # 欣欣
    "2903.TW",  # 遠百
    "2905.TW",  # 三商
    "2906.TW",  # 高林
    "2908.TW",  # 特力
    "2910.TW",  # 統領
    "2911.TW",  # 麗嬰房
    "2912.TW",  # 統一超
    "2913.TW",  # 農林
    "2915.TW",  # 潤泰全
    "2936.TW",  # 客思達-KY
    "2937.TW",  # 集雅社
    "2939.TW",  # 凱羿-KY
    "3002.TW",  # 歐格
    "3003.TW",  # 健和興
    "3004.TW",  # 豐達科
    "3005.TW",  # 神基
    "3006.TW",  # 晶豪科
    "3008.TW",  # 大立光
    "3010.TW",  # 華立
    "3011.TW",  # 今皓
    "3013.TW",  # 晟銘電
    "3014.TW",  # 聯陽
    "3015.TW",  # 全漢
    "3016.TW",  # 嘉晶
    "3017.TW",  # 奇鋐
    "3018.TW",  # 同開
    "3019.TW",  # 亞光
    "3021.TW",  # 鴻名
    "3022.TW",  # 威強電
    "3023.TW",  # 信邦
    "3024.TW",  # 憶聲
    "3025.TW",  # 星通
    "3026.TW",  # 禾伸堂
    "3027.TW",  # 盛達
    "3028.TW",  # 增你強
    "3029.TW",  # 零壹
    "3030.TW",  # 德律
    "3031.TW",  # 佰鴻
    "3032.TW",  # 偉訓
    "3033.TW",  # 威健
    "3034.TW",  # 聯詠
    "3035.TW",  # 智原
    "3036.TW",  # 文曄
    "3037.TW",  # 欣興
    "3038.TW",  # 全台
    "3040.TW",  # 遠見
    "3041.TW",  # 揚智
    "3042.TW",  # 晶技
    "3043.TW",  # 科風
    "3044.TW",  # 健鼎
    "3045.TW",  # 台灣大
    "3046.TW",  # 建碁
    "3047.TW",  # 訊舟
    "3048.TW",  # 益登
    "3049.TW",  # 和鑫
    "3050.TW",  # 鈺德
]
# ============================================

YEARS_FOR_PAYOUT = 5       # 平均配息率使用年數
YIELD_THRESHOLD = 0.06     # 6%
STATE_FILE = Path("state.json")
# ====================================


# ---------- Data fetch helpers ----------
def safe_info(tk: yf.Ticker) -> dict:
    try:
        return tk.info or {}
    except Exception:
        return {}


def get_price(tk: yf.Ticker):
    info = safe_info(tk)
    return info.get("currentPrice") or info.get("regularMarketPrice")


def get_trailing_eps(tk: yf.Ticker):
    info = safe_info(tk)
    return info.get("trailingEps")


def get_shares_outstanding(tk: yf.Ticker):
    info = safe_info(tk)
    sh = info.get("sharesOutstanding")
    return float(sh) if isinstance(sh, (int, float)) and sh > 0 else None


def get_dividend_by_year(dividends: pd.Series):
    """Return {year: total_dividend_per_share}"""
    if dividends is None or dividends.empty:
        return {}
    df = dividends.reset_index()
    df.columns = ["Date", "Dividend"]
    df["Year"] = df["Date"].dt.year
    return df.groupby("Year")["Dividend"].sum().to_dict()


def avg_payout_ratio(div_by_year: dict, eps_ttm: float, years: int):
    """Average payout ratio over last N years: annual_dividend / eps_ttm."""
    if not div_by_year or not eps_ttm or eps_ttm <= 0:
        return None

    cur_year = datetime.now().year
    ratios = []
    for y in range(cur_year - 1, cur_year - 1 - years, -1):
        if y in div_by_year:
            ratios.append(div_by_year[y] / eps_ttm)

    if not ratios:
        return None
    return sum(ratios) / len(ratios)


def latest_dividend_snapshot(div_by_year: dict):
    """Return (latest_year, latest_year_total_dividend)."""
    if not div_by_year:
        return None, 0.0
    y = max(div_by_year.keys())
    return int(y), float(div_by_year[y])


def latest_news_ts(tk: yf.Ticker):
    """Return latest news publish timestamp (epoch seconds), if available."""
    try:
        news = tk.news or []
    except Exception:
        news = []

    if not news:
        return None

    times = []
    for item in news:
        t = item.get("providerPublishTime")
        if isinstance(t, (int, float)):
            times.append(int(t))
    return max(times) if times else None


# ---------- Next-quarter EPS estimation (yfinance-only) ----------
def estimate_next_quarter_eps_from_quarterly(tk: yf.Ticker):
    """Estimate next-quarter EPS using quarterly net income / shares.

    Steps:
      1) sharesOutstanding from tk.info
      2) quarterly income statement net income row
      3) quarter EPS series = netIncome / shares
      4) next-quarter EPS = conservative weighted moving average of recent quarters

    Returns:
      (eps_q_series, next_q_eps_est)
      - eps_q_series: list[float] (most recent first)
      - next_q_eps_est: float
      or (None, None) if insufficient.
    """
    shares = get_shares_outstanding(tk)
    if not shares:
        return None, None

    stmt = None
    try:
        stmt = tk.quarterly_income_stmt
    except Exception:
        stmt = None

    if stmt is None or getattr(stmt, "empty", True):
        try:
            stmt = tk.quarterly_financials  # older yfinance
        except Exception:
            stmt = None

    if stmt is None or getattr(stmt, "empty", True):
        return None, None

    # Find net income row (yfinance label varies)
    net_income_row = None
    for key in [
        "Net Income",
        "NetIncome",
        "Net Income Common Stockholders",
        "Net Income Continuous Operations",
    ]:
        if key in stmt.index:
            net_income_row = key
            break

    if net_income_row is None:
        return None, None

    net_incomes = stmt.loc[net_income_row].dropna()
    if net_incomes.empty:
        return None, None

    # Compute quarter EPS series (most recent first in many yfinance outputs)
    eps_q_series = (net_incomes.astype(float) / shares).tolist()

    if len(eps_q_series) < 2:
        return eps_q_series, float(eps_q_series[-1])

            # Simple average of recent 3 quarters (align with "use first three quarters to estimate next")
    recent = eps_q_series[:3]
    if not recent:
        return None, None
    next_q_eps_est = sum(recent) / len(recent)

    return eps_q_series, float(next_q_eps_est)


# ---------- Yield engine ----------
def estimate_yield_for_symbol(symbol: str, years_for_payout: int, trigger_reasons=None):
    """Compute estimated yield based on Next-Q EPS estimate.

    Logic:
      - Get price and trailingEps (TTM)
      - Estimate next-quarter EPS (from quarterly statements)
        - fallback to base_q_eps = trailingEps/4 if quarterly data missing
      - next_year_eps_est = next_q_eps_est * 4
      - payout_ratio = avg dividend payout ratio from last N years
      - estimated_dividend = next_year_eps_est * payout_ratio
      - estimated_yield = estimated_dividend / price

    Returns: (row_dict_or_None, tk)
    """
    tk = yf.Ticker(symbol)

    price = get_price(tk)
    eps_ttm = get_trailing_eps(tk)
    dividends = tk.dividends

    if not price or not eps_ttm or eps_ttm <= 0:
        return None, tk

    # Next-quarter EPS estimate (yfinance-only, from quarterly net income)
    eps_q_series, next_q_eps_est = estimate_next_quarter_eps_from_quarterly(tk)

    base_q_eps = float(eps_ttm) / 4.0

    # Fallback: if quarterly data missing, use base_q_eps
    if next_q_eps_est is None:
        next_q_eps_est = base_q_eps

    next_year_eps_est = float(next_q_eps_est) * 4.0

    # payout ratio
    div_by_year = get_dividend_by_year(dividends)
    payout = avg_payout_ratio(div_by_year, float(eps_ttm), years_for_payout)
    if payout is None:
        return None, tk

    est_dividend = float(next_year_eps_est) * float(payout)
    est_yield = float(est_dividend) / float(price)

    row = {
        "symbol": symbol,
        "price": round(float(price), 2),

        # historical / baseline
        "trailing_eps_ttm": round(float(eps_ttm), 2),
        "base_q_eps": round(float(base_q_eps), 3),

        # next-quarter estimate (what your project claims)
        "next_q_eps_est": round(float(next_q_eps_est), 3),
        "next_year_eps_est": round(float(next_year_eps_est), 2),

        # payout + yield
        "avg_payout_ratio": round(float(payout), 3),
        "est_dividend": round(float(est_dividend), 2),
        "est_yield_%": round(float(est_yield) * 100, 2),
    }

    return row, tk


def yield_mode(symbols, years_for_payout, yield_threshold):
    rows = []
    for sym in symbols:
        try:
            row, _tk = estimate_yield_for_symbol(sym, years_for_payout, trigger_reasons=None)
            if row is not None:
                rows.append(row)
        except Exception as e:
            print(f"[WARN] {sym}: {e}")

    df_all = pd.DataFrame(rows)
    if not df_all.empty:
        df_all = df_all.sort_values("est_yield_%", ascending=False)

    print("\n=== All Estimated Yields (Next-Q EPS -> Next-Year EPS) ===")
    print(df_all if not df_all.empty else "(no valid rows)")

    if not df_all.empty:
        df_high = df_all[df_all["est_yield_%"] >= yield_threshold * 100]
    else:
        df_high = pd.DataFrame()

    print(f"\n=== High Yield (>= {int(yield_threshold*100)}%) ===")
    print(df_high if not df_high.empty else "(none)")

    return df_all, df_high


# ---------- Event-driven controller ----------
def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_state(state: dict):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def detect_triggers(symbol: str, eps_now, latest_div_year, latest_div_amt, news_ts_now, state: dict):
    """Compare current snapshot vs previous snapshot.

    Triggers:
      - EPS change (trailingEps)
      - Dividend latest year or amount change
      - News timestamp updated (aux)
    """
    prev = state.get(symbol, {})
    reasons = []

    # EPS trigger
    eps_prev = prev.get("trailing_eps_ttm")
    if eps_now is not None and eps_prev is not None:
        if round(float(eps_now), 4) != round(float(eps_prev), 4):
            reasons.append(f"EPS updated: {eps_prev} -> {eps_now}")
    elif eps_now is not None and eps_prev is None:
        reasons.append("EPS became available")

    # Dividend trigger
    div_year_prev = prev.get("latest_div_year")
    div_amt_prev = prev.get("latest_div_amt")
    if latest_div_year is not None:
        if div_year_prev is None:
            reasons.append("Dividend history became available")
        else:
            if int(latest_div_year) != int(div_year_prev):
                reasons.append(f"Dividend year updated: {div_year_prev} -> {latest_div_year}")
            if div_amt_prev is not None and round(float(latest_div_amt), 4) != round(float(div_amt_prev), 4):
                reasons.append(f"Dividend amount updated: {div_amt_prev} -> {latest_div_amt}")

    # News trigger (aux)
    news_prev = prev.get("latest_news_ts")
    if news_ts_now is not None and news_prev is not None:
        if int(news_ts_now) > int(news_prev):
            reasons.append("New news item detected")
    elif news_ts_now is not None and news_prev is None:
        reasons.append("News became available")

    return (len(reasons) > 0), reasons


def update_state_for_symbol(symbol: str, eps_now, latest_div_year, latest_div_amt, news_ts_now, state: dict):
    state[symbol] = {
        "trailing_eps_ttm": eps_now,
        "latest_div_year": latest_div_year,
        "latest_div_amt": latest_div_amt,
        "latest_news_ts": news_ts_now,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def event_mode(symbols, years_for_payout, yield_threshold, force_recalc_all=False):
    """Event-driven mode:
    - Detect triggers for each symbol
    - Recalculate yield only for triggered (or all if force_recalc_all)
    - Update state.json
    """
    state = load_state()
    triggered_symbols = []
    trigger_log = []

    # First pass: detect triggers
    for sym in symbols:
        try:
            tk = yf.Ticker(sym)

            eps_now = get_trailing_eps(tk)
            div_by_year = get_dividend_by_year(tk.dividends)
            latest_year, latest_amt = latest_dividend_snapshot(div_by_year)
            news_ts_now = latest_news_ts(tk)

            triggered, reasons = detect_triggers(sym, eps_now, latest_year, latest_amt, news_ts_now, state)
            update_state_for_symbol(sym, eps_now, latest_year, latest_amt, news_ts_now, state)

            if force_recalc_all:
                triggered = True
                if not reasons:
                    reasons = ["Forced recalculation"]

            if triggered:
                triggered_symbols.append(sym)
                trigger_log.append({"symbol": sym, "reasons": reasons})

        except Exception as e:
            trigger_log.append({"symbol": sym, "reasons": [f"ERROR: {e}"]})

    save_state(state)

    # Second pass: recalc yields for triggered
    rows = []
    for sym in triggered_symbols:
        try:
            reasons = next((x["reasons"] for x in trigger_log if x["symbol"] == sym), [])
            row, _tk = estimate_yield_for_symbol(sym, years_for_payout, trigger_reasons=reasons)
            if row is not None:
                rows.append(row)
        except Exception as e:
            trigger_log.append({"symbol": sym, "reasons": [f"RECALC ERROR: {e}"]})

    df_trig = pd.DataFrame(rows)
    if not df_trig.empty:
        df_trig = df_trig.sort_values("est_yield_%", ascending=False)

    print("\n=== Triggered Symbols (this run) ===")
    print(triggered_symbols if triggered_symbols else "(none)")

    print("\n=== Trigger Reasons ===")
    for item in trigger_log:
        print(f"- {item['symbol']}: " + " | ".join(item["reasons"]))

    print("\n=== Recalculated Yields (Triggered, Next-Q EPS based) ===")
    print(df_trig if not df_trig.empty else "(no triggered & valid rows)")

    if not df_trig.empty:
        df_high = df_trig[df_trig["est_yield_%"] >= yield_threshold * 100]
    else:
        df_high = pd.DataFrame()

    print(f"\n=== High Yield among Triggered (>= {int(yield_threshold*100)}%) ===")
    print(df_high if not df_high.empty else "(none)")

    return df_trig, df_high


# ---------- CLI ----------
def parse_args():
    p = argparse.ArgumentParser(
        description="Taiwan stock selector (yfinance-only): estimate next-quarter EPS -> estimate yield, with event-driven trigger."
    )
    p.add_argument(
        "--mode",
        choices=["yield", "event"],
        default="event",
        help="yield: compute for all symbols; event: detect updates and recalc only triggered symbols",
    )
    p.add_argument(
        "--symbols",
        type=str,
        default="",
        help="Optional comma-separated symbols, e.g., 2330.TW,2317.TW",
    )
    p.add_argument("--years", type=int, default=YEARS_FOR_PAYOUT, help="Years for payout ratio averaging")
    p.add_argument(
        "--threshold",
        type=float,
        default=YIELD_THRESHOLD,
        help="Yield threshold (e.g., 0.06 for 6%%)",
    )
    p.add_argument(
        "--force-all",
        action="store_true",
        help="(event mode) force recalculation for all symbols this run",
    )
    return p.parse_args()


def main():
    args = parse_args()
    symbols = SYMBOLS
    if args.symbols.strip():
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    if args.mode == "yield":
        yield_mode(symbols, args.years, args.threshold)
    else:
        event_mode(symbols, args.years, args.threshold, force_recalc_all=args.force_all)


if __name__ == "__main__":
    main()
