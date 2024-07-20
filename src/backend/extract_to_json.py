import sqlite3
import json
import os
#from utlis.config import DB_PATH

DATABASE_PATH = os.getenv('DB_PATH') + '/chroma.sqlite3'

def extract_metadata_to_json():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        query = "SELECT metadata, topic FROM embeddings_queue"
        cursor.execute(query)
        rows = cursor.fetchall()
        
        metadata_list = []
        for row in rows:
            metadata = json.loads(row[0])
            topic = row[1]
            # Remove 'persistent://default/default/' part from topic
            important_topic_part = topic.replace('persistent://default/default/', '')
            metadata['topic'] = important_topic_part
            metadata_list.append(metadata)
        
        with open('metadata.json', 'w') as f:
            json.dump(metadata_list, f, indent=4)
        
        conn.close()
        print(f"Extracted {len(metadata_list)} records to metadata.json")
    except Exception as e:
        print(f"Error extracting metadata to JSON: {e}")
   
    return os.getcwd() +'/metadata.json'
# if __name__ =='__main__':
#     extract_metadata_to_json()

