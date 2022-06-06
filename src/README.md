# 系統設計

## BigTable 架構

此系統為投票系統，因此 Column 紀錄的是票選項目，Row 紀錄的則是每一個投票人的投票紀錄。

- ```Column``` 表示某票選項目 (ex. 台北市長)

- ```Column Family``` 中則包含同一個類型的投票項目

    > 假如某選舉活動為公投綁大選
    > - 多個公投票選項目會彙整在同一個 ```Column Family```
    >   - 通常不會有跨年的投票結果
    > - 多個大選票選項目會彙整在同一個 ```Column Family```
    >   - 跨年的投票結果使用不同的```TimeStamp```儲存

- ```Row Key``` 則以某人的身分證字號表示，同時會加上該投票區之區域碼作為前綴，讓屬於同一投票區的投票人資訊聚集在一起，以加速後續統計時查找資料的效率
    
    > e.g. 100#A123456789 -> # 之前為投票區域碼 / # 之後為身分證字號

- ```TimeStamp``` 表示的是某投票人在某個投票項目的所有歷史紀錄，因此除了可以取得最新一筆紀錄外，若是要應用於民調票選系統，可以進一步分析多個 ```TimeStamp``` 下各個候選人的得票率，便可以看出隨時間演進的民調變化

- 最後，```Content``` 紀錄的是所選的候選人 ID 。因此對於某投票人在某投票項目的最新一筆資料，儲存的內容會是一個 ID Number，表示的是所選的候選人 ID

