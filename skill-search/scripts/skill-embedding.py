import json
import boto3
import time
from typing import List, Dict, Any

# --- Configurable parameters ---
VECTOR_BUCKET = "my-skill-vector-bucket"
VECTOR_INDEX = "skills-index"  # name of the vector index inside that bucket
EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"
EMBEDDING_DIM = 1024  # must match what the model returns
REGION = "us-east-1"  # or your AWS region
MAX_PUT_BATCH = 50  # how many vectors to put per batch (you can tune)

# --- Setup AWS clients ---
bedrock = boto3.client("bedrock-runtime", region_name=REGION)
s3vectors = boto3.client("s3vectors", region_name=REGION)

# --- Helper: flattening the hierarchical skills-master ---
def flatten_skills(master_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Given the top-level list from skills-master.json, recursively flatten into
    a list of nodes containing id, level, title, description, parent_id, ancestor_ids.
    """
    flat = []
    def recurse(node: Dict[str, Any], parent_id: str, ancestor_ids: List[str]):
        this = {
            "id": node["id"],
            "level": node["level"],
            "title": node.get("title", ""),
            "description": node.get("description", ""),
            "parent_id": parent_id,
            "ancestor_ids": ancestor_ids.copy()
        }
        flat.append(this)
        # If this has children, descend
        for child in node.get("skills", []):
            recurse(child, node["id"], ancestor_ids + [node["id"]])
    for top in master_list:
        recurse(top, parent_id=None, ancestor_ids=[])
    return flat

# --- Helper: compose text for embedding for a skill node ---
def compose_embedding_text(node: Dict[str, Any], skill_map: Dict[str, Dict[str, Any]]) -> str:
    """
    Produce the string to send to embedding model for a skill node.
    Embed title + description + context (parents).
    """
    parts = []
    parts.append(f"{node['title']} (Level {node['level']}). {node['description']}")
    if node["parent_id"]:
        parent = skill_map[node["parent_id"]]
        parts.append(f"Parent (level {parent['level']}): {parent['title']}.")
    # optionally include grandparent title
    if node["ancestor_ids"]:
        # just include path titles
        titles = [skill_map[a]["title"] for a in node["ancestor_ids"]]
        parts.append("Ancestors: " + " > ".join(titles))
    return " ".join(parts)

# --- Step 1: load your skills-master.json from local file (or S3) ---
with open("skills-master.json", "r", encoding="utf-8") as f:
    master = json.load(f)

flattened = flatten_skills(master)
# Build map id → node
skill_map = { node["id"]: node for node in flattened }

# --- Step 2: embed in batches ---
def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Call Bedrock to embed a batch of texts.
    Returns a list of embedding vectors (list of floats).
    """
    # Build request body as JSON with list of inputText
    payload = {"inputText": texts}
    response = bedrock.invoke_model(modelId=EMBEDDING_MODEL_ID, body=json.dumps(payload))
    body = json.loads(response["body"].read())
    embeddings = body["embedding"]  # if single; or list if batch (depends on API spec)
    # If the API returns one embedding (for one text), wrap into list
    if isinstance(embeddings[0], float):
        embeddings = [embeddings]
    return embeddings

# --- Step 3: put vectors into S3 Vectors index ---
def put_vectors_batch(records: List[Dict[str, Any]]):
    """
    records is a list of dicts with keys: id, vector, metadata
    Use s3vectors.put_vectors to insert them.
    """
    put_items = []
    for rec in records:
        put_items.append({
            "key": rec["id"],  # this is the canonical skill ID
            "data": {"float32": rec["vector"]},
            "metadata": rec["metadata"]
        })
    resp = s3vectors.put_vectors(
        vectorBucketName=VECTOR_BUCKET,
        indexName=VECTOR_INDEX,
        vectors=put_items
    )
    return resp

# --- Main loop: batch and upload ---
records_to_upload = []
for node in flattened:
    text = compose_embedding_text(node, skill_map)
    # For simplicity, embed one by one, but you may batch
    emb = embed_texts([text])[0]
    # Cast to float32 (if using numpy, you can do astype)
    # but here ensure the list elements are floats
    vec = [float(x) for x in emb]
    rec = {
        "id": node["id"],
        "vector": vec,
        "metadata": {
            "level": node["level"],
            "title": node["title"],
            "parent_id": node["parent_id"],
            "ancestor_ids": node["ancestor_ids"]
        }
    }
    records_to_upload.append(rec)

    # If batch size hit, flush
    if len(records_to_upload) >= MAX_PUT_BATCH:
        put_vectors_batch(records_to_upload)
        records_to_upload = []

# Upload the remainder
if records_to_upload:
    put_vectors_batch(records_to_upload)

print("All skill embeddings uploaded to S3 vector index.")

# --- (Optional) Also dump a JSONL file locally for debugging / fallback ---
with open("skills-embeddings.jsonl", "w", encoding="utf-8") as fout:
    for rec in flattened:
        # find the rec we embedded
        # Add vector + metadata
        emb_idx = next(r for r in records_to_upload + flattened if r["id"] == rec["id"])
        out = {
            "id": rec["id"],
            "level": rec["level"],
            "title": rec["title"],
            "description": rec["description"],
            "parent_id": rec["parent_id"],
            "ancestor_ids": rec["ancestor_ids"],
            "vector": emb_idx["vector"],
            "metadata": {
                "parent_id": rec["parent_id"],
                "ancestor_ids": rec["ancestor_ids"]
            }
        }
        fout.write(json.dumps(out) + "\n")
