import { useState } from 'react';
import api from '../api';

const BODY_PARTS = [
    { label: 'Head/Neck', index: 0 },
    { label: 'Trunk', index: 1 },
    { label: 'Upper Extremity', index: 2 },
    { label: 'Lower Extremity', index: 3 },
    { label: 'Genitals/Perineal', index: 4 },
    { label: 'Palms/Soles', index: 5 },
    { label: 'Scalp', index: 6 },
    { label: 'Unspecified', index: 7 },
];

export default function Diagnosis() {
    const [file, setFile] = useState(null);
    const [symptoms, setSymptoms] = useState('');
    const [vector, setVector] = useState(new Array(8).fill(0));
    const [result, setResult] = useState(null);

    const togglePart = (index) => {
        const newVector = [...vector];
        newVector[index] = newVector[index] === 0 ? 1 : 0;
        setVector(newVector);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!file) return alert("Vui lòng chọn ảnh!");

        const formData = new FormData();
        formData.append('image', file);
        formData.append('symptoms', symptoms);
        formData.append('body_vector', JSON.stringify(vector)); // Gửi vector dạng [0,1,0...]

        try {
            const response = await api.post('/diagnosis/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setResult(response.data);
        } catch (err) {
            console.error(err);
            alert("Lỗi chẩn đoán");
        }
    };

    return (
        <div style={{ padding: '20px', border: '1px solid #ddd' }}>
            <h2>AI Diagnosis</h2>
            <form onSubmit={handleSubmit}>
                <input type="file" onChange={(e) => setFile(e.target.files[0])} required />
                <textarea 
                    placeholder="Mô tả triệu chứng..." 
                    onChange={(e) => setSymptoms(e.target.value)} 
                    style={{ width: '100%', margin: '10px 0' }}
                />
                
                <label>Chọn vị trí xuất hiện (Tick các ô):</label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '5px', margin: '10px 0' }}>
                    {BODY_PARTS.map((part) => (
                        <button 
                            key={part.index}
                            type="button"
                            onClick={() => togglePart(part.index)}
                            style={{ 
                                background: vector[part.index] ? '#28a745' : '#ccc',
                                color: 'white' 
                            }}
                        >
                            {part.label}
                        </button>
                    ))}
                </div>

                <button type="submit" style={{ width: '100%', marginTop: '10px' }}>Analyze</button>
            </form>

            {result && (
                <div style={{ marginTop: '20px', background: '#e9ecef' }}>
                    <h3>Kết quả: {result.predicted_disease}</h3>
                    <p>Độ tin cậy: {(result.confidence_score * 100).toFixed(2)}%</p>
                    {result.heatmap_url && <img src={`http://localhost:8000${result.heatmap_url}`} width="100%" />}
                </div>
            )}
        </div>
    );
}