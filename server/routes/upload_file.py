from fastapi import APIRouter, UploadFile, File, HTTPException
from data.sample_data import clear_data, add_relationship, get_sample_data
import pandas as pd
import io

router = APIRouter()

@router.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):  
    try:
        print(f"Processing uploaded file: {file.filename}")
        
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
        
        content = await file.read()
        content_str = content.decode('utf-8')
        print(f"File content preview: {content_str[:200]}")
        
        df = pd.read_csv(io.StringIO(content_str))
        print(f"CSV loaded. Shape: {df.shape}, Columns: {list(df.columns)}")
        
        required_columns = ['parent_item', 'child_item', 'sequence_no', 'level']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {missing_columns}"
            )
        clear_data() 
        
        relationships_added = 0
        for _, row in df.iterrows():
            add_relationship(
                parent=str(row['parent_item']),
                child=str(row['child_item']),
                sequence=int(row['sequence_no']),
                level=int(row['level'])
            )
            relationships_added += 1
        
        loaded_data = get_sample_data()
        preview_data = loaded_data[:3]
        
        return {
            "message": "CSV uploaded successfully!",
            "file_name": file.filename,
            "relationships_loaded": relationships_added,
            "preview": preview_data,
            "success": True
        }
    
    except Exception as e:
        print(f"Error processing CSV: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")

@router.get("/data-status")
async def get_data_status():
    current_data = get_sample_data()
    
    if not current_data:
        return {
            "status": "No data loaded",
            "data_source": "Empty - upload CSV to populate",
            "relationships_count": 0
        }
    
    return {
        "status": "Data loaded",
        "data_source": "CSV upload or sample data",
        "relationships_count": len(current_data),
        "sample_relationships": current_data[:3]
    }