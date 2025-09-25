current_data = [
    {"parent_item": "MAT000001", "child_item": "MAT000004", "sequence_no": 1, "level": 1},
    {"parent_item": "MAT000001", "child_item": "MAT000007", "sequence_no": 10, "level": 1},
    {"parent_item": "MAT000001", "child_item": "MAT000008", "sequence_no": 11, "level": 1},
    {"parent_item": "MAT000002", "child_item": "MAT000017", "sequence_no": 1, "level": 2},
    {"parent_item": "MAT000004", "child_item": "MAT000018", "sequence_no": 1, "level": 2},
]
def get_sample_data():
    return current_data

def add_relationship(parent, child, sequence, level):
    new_item = {
        "parent_item": parent,
        "child_item": child, 
        "sequence_no": sequence,
        "level": level
    }
    current_data.append(new_item)
    return new_item

def clear_data():
    global sample_data
    current_data = []
    print("data cleared")

def get_data_info():
    return {
        "total_relationships": len(current_data),
        "data_preview": current_data[:10] if current_data else [],
        "is_empty": len(current_data) == 0
    }