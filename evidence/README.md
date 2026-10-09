# 初期資料の検証証拠

bootstrap-readback.json は、初期資料の保存commitを固定して各ファイルを読み戻した記録。
receipt自身を含むcommitの自己検証を主張しない。
元の内容commit、初期main、比較したファイル、読み戻したblob SHAと一致結果を記録する。
receiptを追加した後は、branch head、receipt内容、PR、mainが変わっていないことを別途読み戻す。
retry=0、fallback=disabled。結果不明の外部mutationを自動再送しない。
