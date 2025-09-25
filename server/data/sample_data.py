sample_data = [
    {"parent_item": "MAT000001", "child_item": "MAT000004", "sequence_no": 1, "level": 1},
    {"parent_item": "MAT000001", "child_item": "MAT000007", "sequence_no": 10, "level": 1},
    {"parent_item": "MAT000001", "child_item": "MAT000008", "sequence_no": 11, "level": 1},
    {"parent_item": "MAT000002", "child_item": "MAT000017", "sequence_no": 1, "level": 2},
    {"parent_item": "MAT000004", "child_item": "MAT000018", "sequence_no": 1, "level": 2},
]
def get_sample_data():
    """
    Return the sample data
    In the future, this could load from database, CSV file, etc.
    """
    return sample_data

def add_relationship(parent, child, sequence, level):
    """
    Add new relationship to data
    Useful for testing or when we add CSV upload
    """
    new_item = {
        "parent_item": parent,
        "child_item": child, 
        "sequence_no": sequence,
        "level": level
    }
    sample_data.append(new_item)
    return new_item

def clear_data():
    """
    Clear all data (useful for testing)
    """
    global sample_data
    sample_data = []