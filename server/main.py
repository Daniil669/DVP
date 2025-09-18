from fastapi import FastAPI

app = FastAPI()

sample_data=[
    {"parent_item": "MAT000001", "child_item": "MAT000004", "sequence_no": 1, "level": 1},
    {"parent_item": "MAT000001", "child_item": "MAT000007", "sequence_no": 10, "level": 1},
    {"parent_item": "MAT000001", "child_item": "MAT000008", "sequence_no": 11, "level": 1},
    {"parent_item": "MAT000001", "child_item": "MAT000002", "sequence_no": 2, "level": 1},
    {"parent_item": "MAT000002", "child_item": "MAT000017", "sequence_no": 1, "level": 2},
    {"parent_item": "MAT000003", "child_item": "MAT000006", "sequence_no": 1, "level": 2},
    {"parent_item": "MAT000004", "child_item": "MAT000018", "sequence_no": 1, "level": 2},
]

def get_node_children(node_id: str):
    children = []
    for node in sample_data:
        if node["parent"] == node_id:
            children.append(node)
    return children

def get_root_nodes():
    roots = []
    for node in sample_data:
        if node["parent"] is None:
            roots.append(node)
    return roots

@app.get("/")
def hello():
    return {"message": "it is working yeahhhhhh"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port = 8000)
