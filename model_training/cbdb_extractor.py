import glob
import json
import sqlite3
import sys

import pandas as pd
from tqdm import tqdm

sys.stdout.reconfigure(encoding="utf-8")


class CBDBDataExtractor:
    def __init__(self, db_path=None):
        if db_path is None:
            db_files = glob.glob("*.sqlite3") + glob.glob("*.db")
            if not db_files:
                raise FileNotFoundError(
                    "No SQLite database file found in current directory."
                )
            db_path = db_files[0]

        self.db_path = db_path
        print(f"Connecting to database: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def extract_instruction_qa(
        self, output_path="cbdb_instruction_qa.jsonl", limit=20000
    ):
        """
        Extracts biographical QA pairs for fine-tuning Causal LMs / Instruct models.
        """
        print("Extracting biographical instruction Q&A pairs...")
        cursor = self.conn.cursor()

        query = """
        SELECT
            p.c_personid,
            p.c_name,
            p.c_name_chn,
            p.c_birthyear,
            p.c_deathyear,
            p.c_index_year,
            p.c_female,
            d.c_dynasty_chn,
            p.c_notes
        FROM BIOG_MAIN p
        LEFT JOIN DYNASTIES d ON p.c_dy = d.c_dy
        WHERE p.c_name_chn IS NOT NULL AND p.c_name_chn != ''
        LIMIT ?
        """
        cursor.execute(query, (limit,))
        persons = cursor.fetchall()

        # Fetch office postings
        offices_by_person = {}
        office_query = """
        SELECT po.c_personid, o.c_office_chn, po.c_firstyear, po.c_lastyear
        FROM POSTED_TO_OFFICE_DATA po
        JOIN OFFICE_CODES o ON po.c_office_id = o.c_office_id
        WHERE po.c_personid IN (SELECT c_personid FROM BIOG_MAIN WHERE c_name_chn IS NOT NULL LIMIT ?)
        LIMIT 50000
        """
        try:
            cursor.execute(office_query, (limit,))
            for row in cursor.fetchall():
                pid = row["c_personid"]
                if pid not in offices_by_person:
                    offices_by_person[pid] = []
                offices_by_person[pid].append(row)
        except Exception as e:
            print(f"Warning fetching offices: {e}")

        # Fetch kinship
        kin_by_person = {}
        kin_query = """
        SELECT k.c_personid, kc.c_kinrel_chn, p2.c_name_chn as kin_name
        FROM KIN_DATA k
        JOIN KINSHIP_CODES kc ON k.c_kin_code = kc.c_kincode
        JOIN BIOG_MAIN p2 ON k.c_kin_id = p2.c_personid
        WHERE k.c_personid IN (SELECT c_personid FROM BIOG_MAIN WHERE c_name_chn IS NOT NULL LIMIT ?)
        LIMIT 50000
        """
        try:
            cursor.execute(kin_query, (limit,))
            for row in cursor.fetchall():
                pid = row["c_personid"]
                if pid not in kin_by_person:
                    kin_by_person[pid] = []
                kin_by_person[pid].append(row)
        except Exception as e:
            print(f"Warning fetching kinship: {e}")

        records = []
        for p in tqdm(persons, desc="Building QA pairs"):
            pid = p["c_personid"]
            name_chn = p["c_name_chn"]
            name_pinyin = p["c_name"] if p["c_name"] else ""
            dynasty = p["c_dynasty_chn"] if p["c_dynasty_chn"] else "未知朝代"
            birth = (
                p["c_birthyear"] if p["c_birthyear"] and p["c_birthyear"] != 0 else None
            )
            death = (
                p["c_deathyear"] if p["c_deathyear"] and p["c_deathyear"] != 0 else None
            )
            index_yr = (
                p["c_index_year"]
                if p["c_index_year"] and p["c_index_year"] != 0
                else None
            )
            gender = "女" if p["c_female"] == 1 else "男"

            # Construct summary
            lifespan_str = ""
            if birth and death:
                lifespan_str = f"生卒年约为公元 {birth} 年至 {death} 年"
            elif birth:
                lifespan_str = f"生于约公元 {birth} 年"
            elif death:
                lifespan_str = f"卒于约公元 {death} 年"
            elif index_yr:
                lifespan_str = f"活跃指数年约为公元 {index_yr} 年"

            offices = offices_by_person.get(pid, [])
            office_strs = [
                off["c_office_chn"] for off in offices if off["c_office_chn"]
            ]
            office_desc = (
                "、".join(office_strs[:5]) if office_strs else "暂无明确官职记录"
            )

            kins = kin_by_person.get(pid, [])
            kin_strs = [
                f"{k['kin_name']}（{k['c_kinrel_chn']}）"
                for k in kins
                if k["kin_name"] and k["c_kinrel_chn"]
            ]
            kin_desc = "、".join(kin_strs[:5]) if kin_strs else "暂无详细亲属记录"

            prompt = f"请介绍一下中国历史人物【{name_chn}】（{name_pinyin}）的生平背景、朝代及官职。"

            response_text = f"【{name_chn}】"
            if name_pinyin:
                response_text += f"（Pinyin: {name_pinyin}）"
            response_text += f"，性别：{gender}，是{dynasty}时期的人物。"
            if lifespan_str:
                response_text += f"{lifespan_str}。"
            response_text += f"\n- 曾任官职：{office_desc}。"
            response_text += f"\n- 主要亲属：{kin_desc}。"
            if (
                p["c_notes"]
                and isinstance(p["c_notes"], str)
                and len(p["c_notes"].strip()) > 5
            ):
                clean_notes = p["c_notes"].replace("\x7f", "").strip()
                if len(clean_notes) < 200:
                    response_text += f"\n- 备注史料：{clean_notes}"

            records.append(
                {
                    "instruction": prompt,
                    "input": "",
                    "output": response_text,
                    "meta": {"person_id": pid, "dynasty": dynasty, "name": name_chn},
                }
            )

        with open(output_path, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        print(f"Saved {len(records)} QA pairs to {output_path}")
        return output_path

    def extract_dynasty_classification_data(
        self, output_path="cbdb_dynasty_dataset.csv", limit=50000
    ):
        """
        Extracts structured feature matrix for predicting Dynasty from biographical metadata.
        """
        print("Extracting dynasty classification feature matrix...")
        query = """
        SELECT
            p.c_personid,
            p.c_female,
            p.c_ethnicity_code,
            p.c_index_year,
            p.c_birthyear,
            p.c_deathyear,
            p.c_dy as dynasty_code,
            d.c_dynasty_chn as dynasty_name,
            COALESCE(po.office_count, 0) as office_count,
            COALESCE(kd.kinship_count, 0) as kinship_count,
            COALESCE(ad.assoc_count, 0) as assoc_count
        FROM BIOG_MAIN p
        JOIN DYNASTIES d ON p.c_dy = d.c_dy
        LEFT JOIN (
            SELECT c_personid, COUNT(*) as office_count
            FROM POSTED_TO_OFFICE_DATA GROUP BY c_personid
        ) po ON po.c_personid = p.c_personid
        LEFT JOIN (
            SELECT c_personid, COUNT(*) as kinship_count
            FROM KIN_DATA GROUP BY c_personid
        ) kd ON kd.c_personid = p.c_personid
        LEFT JOIN (
            SELECT c_personid, COUNT(*) as assoc_count
            FROM ASSOC_DATA GROUP BY c_personid
        ) ad ON ad.c_personid = p.c_personid
        WHERE p.c_dy IS NOT NULL AND p.c_dy > 0 AND d.c_dynasty_chn IS NOT NULL
        LIMIT ?
        """
        df = pd.read_sql_query(query, self.conn, params=(limit,))
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"Saved {len(df)} samples to {output_path}")
        return output_path

    def extract_social_graph_edges(
        self, output_path="cbdb_social_graph.csv", limit=100000
    ):
        """
        Extracts edge lists (kinship & social associations) for Graph Neural Network training.
        """
        print("Extracting social network graph edge list...")
        query = """
        SELECT
            c_personid as source_id,
            c_kin_id as target_id,
            'KINSHIP' as relation_category,
            c_kin_code as relation_code
        FROM KIN_DATA
        WHERE c_kin_id IS NOT NULL AND c_kin_id > 0
        LIMIT ?
        """
        df_kin = pd.read_sql_query(query, self.conn, params=(limit,))

        query_assoc = """
        SELECT
            c_personid as source_id,
            c_assoc_id as target_id,
            'ASSOCIATION' as relation_category,
            c_assoc_code as relation_code
        FROM ASSOC_DATA
        WHERE c_assoc_id IS NOT NULL AND c_assoc_id > 0
        LIMIT ?
        """
        df_assoc = pd.read_sql_query(query_assoc, self.conn, params=(limit,))

        df = pd.concat([df_kin, df_assoc], ignore_index=True)
        df.to_csv(output_path, index=False, encoding="utf-8")
        print(f"Saved {len(df)} graph edges to {output_path}")
        return output_path

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    extractor = CBDBDataExtractor()
    extractor.extract_instruction_qa(limit=10000)
    extractor.extract_dynasty_classification_data(limit=30000)
    extractor.extract_social_graph_edges(limit=50000)
    extractor.close()
    print("All dataset extraction completed successfully!")
