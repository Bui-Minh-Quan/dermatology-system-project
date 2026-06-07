import os
import json
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

class RAGDataLoader:
    def __init__(self, chunk_size=300, chunk_overlap=50):
        # Yêu cầu 12: Giảm chunk size xuống 300, overlap 50
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", " ", ""]
        )

    def _dict_to_text(self, data_dict, indent=0):
        """Hàm đệ quy chuyển đổi dict thành text dễ đọc"""
        if not isinstance(data_dict, dict):
            return str(data_dict)
            
        text = ""
        space = " " * indent
        for key, value in data_dict.items():
            clean_key = key.replace('_', ' ').capitalize()
            if isinstance(value, dict):
                text += f"{space}{clean_key}:\n"
                text += self._dict_to_text(value, indent + 2)
            elif isinstance(value, list):
                if value:
                    text += f"{space}{clean_key}: {', '.join(str(v) for v in value)}\n"
            elif value: 
                text += f"{space}{clean_key}: {value}\n"
        return text

    def _extract_base_metadata(self, data, entity_type, filename):
        """Trích xuất các siêu dữ liệu dùng chung"""
        meta = data.get('metadata', {})
        
        # Tự động tìm key chứa tên (disease_name, drug_name, symptom_name)
        name_key = f"{entity_type.lower()}_name"
        entity_name = meta.get(name_key, "Unknown")
        
        # Xử lý trường hợp severity có thể là string hoặc list tùy file
        severity = meta.get('severity', meta.get('severity_levels', []))
        if isinstance(severity, list):
            severity = ", ".join(severity)

        return {
            "entity_type": entity_type,
            "entity_name": entity_name,
            "canonical_name": meta.get('canonical_name', ""),           # Yêu cầu 8
            "synonyms": meta.get('synonyms', []),                       # Yêu cầu 7
            "category": meta.get('category', ""),                       # Yêu cầu 9
            "severity": severity,                                       # Yêu cầu 10
            "graph_node_type": entity_type,                             # Yêu cầu 13
            "source_file": filename,                                    # Yêu cầu 2
            "created_at": datetime.utcnow().isoformat()                 # Yêu cầu 15
        }

    def process_disease_file(self, filepath, filename):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        base_meta = self._extract_base_metadata(data, "Disease", filename)
        
        # Yêu cầu 4: Tách Disease thành nhiều section chi tiết
        sections = {
            "definition": data.get('definition', ''),
            "overview": data.get('overview', ''),
            "symptoms": ', '.join(data.get('signs_symptoms', [])),
            "causes": self._dict_to_text(data.get('causes_etiology', {})),
            "risk_factors": ', '.join(data.get('risk_factors', [])),
            "diagnosis": self._dict_to_text(data.get('diagnosis', {})),
            "management": self._dict_to_text(data.get('management', {})),
            "complications": ', '.join(data.get('complications', [])),
            "prevention": ', '.join(data.get('prevention', []))
        }
        
        return self._create_chunks(sections, base_meta)

    def process_drug_file(self, filepath, filename):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        base_meta = self._extract_base_metadata(data, "Drug", filename)
        
        # Yêu cầu 5: Tách Drug thành nhiều section chi tiết
        sections = {
            "definition": data.get('definition', ''),
            "mechanism": data.get('mechanism_of_action', ''),
            "indications": ', '.join(data.get('indications', [])),
            "contraindications": ', '.join(data.get('contraindications', [])),
            "side_effects": self._dict_to_text(data.get('side_effects', {})),
            "interactions": ', '.join(data.get('drug_interactions', [])),
            "warnings": ', '.join(data.get('warnings_precautions', [])),
            "patient_education": ', '.join(data.get('patient_education', []))
        }
        
        return self._create_chunks(sections, base_meta)

    def process_symptom_file(self, filepath, filename):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        base_meta = self._extract_base_metadata(data, "Symptom", filename)
        
        # Yêu cầu 6: Tách Symptom thành nhiều section chi tiết
        sections = {
            "definition": data.get('definition', ''),
            "characteristics": ', '.join(data.get('common_characteristics', [])),
            "causes": self._dict_to_text(data.get('possible_causes', {})),
            "associated_symptoms": ', '.join(data.get('associated_symptoms', [])),
            "severity": self._dict_to_text(data.get('severity_indicators', {})),
            "red_flags": ', '.join(data.get('red_flags', [])),
            "management": self._dict_to_text(data.get('general_management', {}))
        }
        
        return self._create_chunks(sections, base_meta)

    def _create_chunks(self, sections, base_meta):
        """Cắt các section thành chunk và đính kèm metadata cực sâu"""
        chunks = []
        entity_type = base_meta['entity_type']
        entity_name = base_meta['entity_name']
        
        for section_type, content in sections.items():
            # Bỏ qua nếu section rỗng
            if not content or not str(content).strip():
                continue
                
            split_texts = self.text_splitter.split_text(str(content))
            
            for idx, text in enumerate(split_texts):
                clean_text = text.strip()
                
                # Yêu cầu 14: Loại bỏ chunk quá ngắn (< 30 ký tự)
                if len(clean_text) < 30:
                    continue
                
                # Yêu cầu 11: Thêm chunk summary định hình context trước khi embed
                contextualized_content = (
                    f"{entity_type}: {entity_name}\n"
                    f"Section: {section_type.replace('_', ' ').capitalize()}\n"
                    f"Summary:\n{clean_text}"
                )
                
                # Yêu cầu 3: Tạo chunk_id duy nhất
                safe_name = entity_name.lower().replace(" ", "_").replace("-", "_")
                chunk_id = f"{entity_type.lower()}_{safe_name}_{section_type}_{idx+1:03d}"
                
                # Copy base_meta và thêm các trường cụ thể của chunk này
                chunk_data = base_meta.copy()
                chunk_data.update({
                    "chunk_id": chunk_id,
                    "section_type": section_type,                             # Yêu cầu 1
                    "content": contextualized_content
                })
                
                chunks.append(chunk_data)
                
        return chunks

    def load_all_data(self):
        all_chunks = []
        
        folder_processors = {
            "diseases": self.process_disease_file,
            "drugs": self.process_drug_file,
            "symptoms": self.process_symptom_file
        }

        for folder_name, processor in folder_processors.items():
            folder_path = os.path.join(DATA_DIR, folder_name)
            if not os.path.exists(folder_path):
                print(f"Warning: Thư mục {folder_path} không tồn tại.")
                continue
                
            print(f"Đang xử lý thư mục: {folder_name}...")
            for filename in os.listdir(folder_path):
                if filename.endswith('.json'):
                    filepath = os.path.join(folder_path, filename)
                    try:
                        # Chuyền thêm filename để bắt source_file
                        chunks = processor(filepath, filename)
                        all_chunks.extend(chunks)
                    except Exception as e:
                        print(f"Lỗi khi xử lý file {filename}: {e}")
                        
        return all_chunks

if __name__ == "__main__":
    loader = RAGDataLoader() # Đã cấu hình mặc định 300/50 ở hàm init
    chunks = loader.load_all_data()
    
    print(f"\nĐã tạo thành công {len(chunks)} chunks.")
    
    print("\n--- TEST PREVIEW ---")
    for i in range(min(2, len(chunks))):
        print(f"Chunk ID: {chunks[i]['chunk_id']}")
        print(f"Source: {chunks[i]['source_file']}")
        print(f"Type: {chunks[i]['entity_type']} | Name: {chunks[i]['entity_name']}")
        print(f"Section: {chunks[i]['section_type']}")
        print(f"Category: {chunks[i]['category']} | Severity: {chunks[i]['severity']}")
        print(f"Synonyms: {chunks[i]['synonyms']}")
        print("--- CONTENT (Sẽ được Embed) ---")
        print(chunks[i]['content'])
        print("=" * 50)