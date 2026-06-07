import os
import json
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

class RAGDataLoader:
    def __init__(self, chunk_size=300, chunk_overlap=50):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", " ", ""]
        )

    def _dict_to_text(self, data_dict, indent=0):
        """Recursively convert a dictionary to a readable text format."""
        if not isinstance(data_dict, dict):
            return str(data_dict)
            
        text = ""
        space = " " * indent
        for key, value in data_dict.items():
            clean_key = key.replace('_', ' ').capitalize()
            if isinstance(value, dict):
                text += f"{space}{clean_key}:\n{self._dict_to_text(value, indent + 2)}"
            elif isinstance(value, list):
                if value:
                    text += f"{space}{clean_key}: {', '.join(str(v) for v in value)}\n"
            elif value: 
                text += f"{space}{clean_key}: {value}\n"
        return text

    def _extract_base_metadata(self, data, entity_type, filename):
        """Extract common metadata fields across all entity types."""
        meta = data.get('metadata', {})
        name_key = f"{entity_type.lower()}_name"
        entity_name = meta.get(name_key, "Unknown")
        
        severity = meta.get('severity', meta.get('severity_levels', []))
        if isinstance(severity, list):
            severity = ", ".join(severity)

        return {
            "entity_type": entity_type,
            "entity_name": entity_name,
            "canonical_name": meta.get('canonical_name', ""),
            "synonyms": meta.get('synonyms', []),
            "category": meta.get('category', ""),
            "severity": severity,
            "graph_node_type": entity_type,
            "source_file": filename,
            "created_at": datetime.utcnow().isoformat()
        }

    def process_disease_file(self, filepath, filename):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        base_meta = self._extract_base_metadata(data, "Disease", filename)
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
        """Split sections into text chunks and attach metadata."""
        chunks = []
        entity_type, entity_name = base_meta['entity_type'], base_meta['entity_name']
        
        for section_type, content in sections.items():
            if not content or not str(content).strip():
                continue
                
            split_texts = self.text_splitter.split_text(str(content))
            for idx, text in enumerate(split_texts):
                clean_text = text.strip()
                if len(clean_text) < 30:
                    continue
                
                contextualized_content = (
                    f"{entity_type}: {entity_name}\n"
                    f"Section: {section_type.replace('_', ' ').capitalize()}\n"
                    f"Summary:\n{clean_text}"
                )
                
                safe_name = entity_name.lower().replace(" ", "_").replace("-", "_")
                chunk_id = f"{entity_type.lower()}_{safe_name}_{section_type}_{idx+1:03d}"
                
                chunk_data = base_meta.copy()
                chunk_data.update({
                    "chunk_id": chunk_id,
                    "section_type": section_type,
                    "content": contextualized_content
                })
                chunks.append(chunk_data)
        return chunks

    def load_all_data(self):
        all_chunks = []
        processors = {
            "diseases": self.process_disease_file,
            "drugs": self.process_drug_file,
            "symptoms": self.process_symptom_file
        }

        for folder_name, processor in processors.items():
            folder_path = os.path.join(DATA_DIR, folder_name)
            if not os.path.exists(folder_path):
                continue
                
            for filename in os.listdir(folder_path):
                if filename.endswith('.json'):
                    all_chunks.extend(processor(os.path.join(folder_path, filename), filename))
        return all_chunks