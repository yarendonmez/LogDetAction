import pandas as pd
from pathlib import Path

hdfs_path = Path(r"C:\developer\LogDetAction\v2.0\HDFS_processed.csv")
cowrie_path = Path(r"C:\developer\LogDetAction\v2.0\Cowrie_processed.csv")

output_path = Path(r"C:\developer\LogDetAction\v2.0\training_dataset.csv")

print("HDFS okunuyor...")
hdfs_df = pd.read_csv(hdfs_path)

print("Cowrie okunuyor...")
cowrie_df = pd.read_csv(cowrie_path)

print("Birleştiriliyor...")
merged_df = pd.concat([hdfs_df, cowrie_df], ignore_index=True)

print("Karıştırılıyor...")
merged_df = merged_df.sample(frac=1, random_state=42).reset_index(drop=True)

print("Kaydediliyor...")
merged_df.to_csv(output_path, index=False, encoding="utf-8-sig", escapechar="\\")

print("\nTamamlandı.")
print("Çıktı:", output_path)

print("\nToplam kayıt:", len(merged_df))

print("\nLabel dağılımı:")
print(merged_df["label"].value_counts())

print("\nDataset dağılımı:")
print(merged_df["dataset"].value_counts())