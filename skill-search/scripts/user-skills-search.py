"""
skills_search.py

- Run locally with AWS profile (Session(profile_name=...))
- Dependencies: boto3, numpy
- Purpose: embed query (Bedrock) -> query S3 Vector index (s3vectors) -> load users from s3 -> score & rank
"""

import os
import json
import math
import boto3
import numpy as np
from collections import defaultdict
from typing import List, Dict, Any, Tuple, Set

# ---------- CONFIG ----------
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_PROFILE = os.getenv("AWS_PROFILE", None)   # set or leave None to use default creds
VECTOR_BUCKET = "your-vector-bucket-name"     # the S3 vector bucket name where you stored skill vectors
VECTOR_INDEX = "skills-index"                 # the vector index name (indexName)
APP_BUCKET = "your-app-bucket"                # bucket containing skills-master.json and users/*
SKILLS_MASTER_KEY = "master/skills-master.json"  # path in APP_BUCKET
USERS_PREFIX = "users/"                        # prefix for user skill files: users/{userId}/skills.json

# Bedrock model ID to use for embeddings (replace with model you have access to)
BEDROCK_EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v1"  # example; change if needed

# Search tuning
TOP_K = 12                 # how many skill vectors to fetch from S3 Vectors
MIN_SIMILARITY = 0.35     # drop very weak matches (tune empirically)

# Scoring constants (tunable)
RATING_MULTIPLIER = {1: 1.0, 2: 1.5, 3: 2.0}
DEPTH_MULTIPLIER = {3: 1.0, 4: 1.25}   # L3 = generic skill, L4 = technology (slightly heavier)
TECH_BONUS_PER_MATCH = 0.05
TECH_BONUS_CAP = 0.20

# ---------- AWS clients ----------
def make_clients(region=AWS_REGION, profile_name=AWS_PROFILE):
    if profile_name:
        session = boto3.Session(profile_name=profile_name, region_name=region)
    else:
        session = boto3.Session(region_name=region)
    s3 = session.client("s3")
    s3vectors = session.client("s3vectors")          # S3 Vector API (put/query)
    bedrock_runtime = session.client("bedrock-runtime")  # invoke_model for embeddings
    return s3, s3vectors, bedrock_runtime

# ---------- Utilities: load master skills & flatten ----------
def load_skills_master(s3, bucket: str, key: str) -> List[Dict[str, Any]]:
    obj = s3.get_object(Bucket=bucket, Key=key)
    text = obj['Body'].read().decode('utf-8')
    data = json.loads(text)
    # data is expected to be list of L1 nodes (per your sample)
    return data

def flatten_skills_tree(master_list: List[Dict[str, Any]]) -> Dict[str, Dict[str,Any]]:
    """
    Walk the nested skills tree and return skillById map:
    skillById[skillId] = {
       id, level, title, description, parent_id (or None), ancestor_ids (ordered L2..L1),
       path_titles: "L1 > L2 > L3",
    }
    This includes nodes at all levels (L1-L4).
    """
    skillById = {}

    def recurse(node, parent_chain):
        # parent_chain: list of (id, title) from L1 .. parent-level
        sid = node['id']
        level = node.get('level')
        title = node.get('title','')
        desc = node.get('description','')
        parent_id = parent_chain[-1][0] if parent_chain else None
        ancestor_ids = [p[0] for p in parent_chain[::-1]]  # nearest first? keep L2, L1 if present
        path_titles = " > ".join([p[1] for p in parent_chain] + [title])
        skillById[sid] = {
            "id": sid,
            "level": level,
            "title": title,
            "description": desc,
            "parent_id": parent_id,
            "ancestor_ids": ancestor_ids,
            "path_titles": path_titles
        }
        # recurse children if present
        for child in node.get("skills", []) or []:
            recurse(child, parent_chain + [(sid, title)])

    for top in master_list:
        recurse(top, [])
    return skillById

# ---------- Load users from S3 and build indices (MVP in-memory) ----------
def list_user_skill_objects(s3, bucket: str, prefix: str) -> List[str]:
    # returns keys under prefix that look like .../skills.json
    keys = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            k = obj['Key']
            if k.endswith('skills.json'):
                keys.append(k)
    return keys

def load_users(s3, bucket: str, users_prefix: str, skillById: Dict[str,Any]):
    """
    Loads user skill files into memory, and derives:
     - user['skillIdSet'] (l3 ids)
     - user['techIdSet'] (l4 ids)
     - user['selected_map'] mapping l3Id -> entry (rating + l4Ids)
    Returns:
      users_list, users_by_l3, users_by_l4
    """
    keys = list_user_skill_objects(s3, bucket, users_prefix)
    users = []
    users_by_l3 = defaultdict(list)
    users_by_l4 = defaultdict(list)
    for key in keys:
        obj = s3.get_object(Bucket=bucket, Key=key)
        data = json.loads(obj['Body'].read().decode('utf-8'))
        # expected schema as provided in prompt
        selected = data.get('selectedSkills', [])
        user = {
            "userEmail": data.get('userEmail'),
            "selectedSkills": selected,
            "lastUpdated": data.get('lastUpdated'),
            "skillIdSet": set(),
            "techIdSet": set(),
            "selected_map": {}
        }
        for entry in selected:
            l3 = entry['l3Id']
            user['skillIdSet'].add(l3)
            user['selected_map'][l3] = {
                "rating": int(entry.get('rating', 1)),
                "l4Ids": list(entry.get('l4Ids', [])),
                "l2Id": entry.get('l2Id'),
                "l1Id": entry.get('l1Id')
            }
            for l4 in entry.get('l4Ids', []):
                user['techIdSet'].add(l4)
                users_by_l4[l4].append(user)
            users_by_l3[l3].append(user)
        users.append(user)
    return users, users_by_l3, users_by_l4

# ---------- Embedding helper (Bedrock) ----------
def embed_text_bedrock(bedrock_runtime, text: str, model_id: str) -> List[float]:
    """
    Uses Bedrock runtime invoke_model to get vector embedding for `text`.
    Model-specific request/response shape may vary. Examples typically return JSON with an 'embedding' field.
    If your model requires a different input key (e.g., 'inputText'), adapt the payload.
    """
    import json
    # Example payload for many bedrock embed models:
    body = json.dumps({"inputText": text})
    response = bedrock_runtime.invoke_model(
        body=body.encode('utf-8'),
        modelId=model_id,
        accept="application/json",
        contentType="application/json"
    )
    # response['body'] is a StreamingBody; read & parse
    resp_text = response['body'].read().decode('utf-8')
    resp_json = json.loads(resp_text)
    # Common places embedding might live:
    embedding = None
    if isinstance(resp_json, dict):
        embedding = resp_json.get('embedding') or resp_json.get('embeddings') or resp_json.get('embedding_vector') or resp_json.get('result')
    if embedding is None:
        # If model returns nested shape, you may need to inspect resp_json and adapt here.
        raise ValueError("Embedding not found in Bedrock response. Response keys: " + ", ".join(resp_json.keys()))
    # Ensure float32 numbers (use numpy)
    return [float(x) for x in embedding]

# ---------- Query S3 Vector index ----------
def query_skill_vectors(s3vectors_client, vector_bucket: str, index_name: str, query_vector: List[float], top_k: int = TOP_K):
    # Query S3 vectors. The vector must match index dimension and be float32.
    # Returns list of dicts: { key, metadata, distance }
    # Using returnMetadata=True to get stored metadata (level, parent_id, ancestor_ids)
    query_vec = np.array(query_vector, dtype=np.float32).tolist()
    resp = s3vectors_client.query_vectors(
        vectorBucketName=vector_bucket,
        indexName=index_name,
        topK=top_k,
        queryVector={"float32": query_vec},
        returnMetadata=True,
        returnDistance=True
    )
    return resp.get('vectors', [])

# ---------- Map hits to canonical L3/L4 candidate hits ----------
def expand_hits_to_candidate_skills(hits: List[Dict[str,Any]], skillById: Dict[str,Any], min_similarity: float = MIN_SIMILARITY):
    """
    Input hits are the S3 Vectors results with key + metadata + distance.
    We transform them into candidate hits where each hit is either an L4 or an L3 (and include similarity).
    S3 Vectors returns distances (smaller = closer for euclidean). If distance metric is cosine, distance = (1 - cosine).
    For simplicity we will treat returned 'distance' as a similarity proxy: similarity = max(0, 1 - distance) if distance given.
    If your index uses cosine and returns (1 - cosine), the transformation below gives approximate cosine similarity.
    """
    candidate_hits = []
    for item in hits:
        key = item.get('key')
        metadata = item.get('metadata') or {}
        distance = item.get('distance')
        # compute simple similarity proxy:
        similarity = None
        if distance is not None:
            # many S3Vectors configs use cosine distance = (1 - cosineSimilarity) or raw distance depending on index config.
            # this heuristic maps distance->similarity but you can tune/replace with exact mapping.
            similarity = max(0.0, 1.0 - float(distance))
        else:
            # fallback: if no distance, set similarity 1.0 (not ideal)
            similarity = 1.0
        if similarity < min_similarity:
            continue
        # metadata should include "level" (1..4) and maybe parent_id or ancestor ids
        level = int(metadata.get('level', skillById.get(key, {}).get('level', 0)))
        parent = metadata.get('parent_id') or skillById.get(key, {}).get('parent_id')
        # append the actual node (preserve both L4 and L3)
        candidate_hits.append({
            "skillId": key,
            "level": level,
            "similarity": similarity,
            "metadata": metadata,
            "parent_l3": None if level == 3 else parent
        })
        # if L4 => also include parent L3 candidate (so L3 match isn't missed)
        if level == 4 and parent:
            # map parent id to L3 by looking up skillById (parent might be L3 directly or you may need to step)
            parent_obj = skillById.get(parent, {})
            if parent_obj and parent_obj.get('level') == 3:
                candidate_hits.append({
                    "skillId": parent_obj['id'],
                    "level": 3,
                    "similarity": similarity * 0.90,  # slightly reduce weight for parent mapping
                    "metadata": parent_obj,
                    "parent_l3": parent_obj['id']
                })
    # dedupe keeping highest similarity per skillId
    by_id = {}
    for h in candidate_hits:
        sid = h['skillId']
        if sid not in by_id or h['similarity'] > by_id[sid]['similarity']:
            by_id[sid] = h
    return list(by_id.values())

# ---------- Scoring ----------
def score_user_against_hits(user: Dict[str,Any], candidate_hits: List[Dict[str,Any]]):
    """
    Applies the scoring formula:
       contribution = similarity * rating_multiplier * depth_multiplier
    Includes technology bonus for matched L4s.
    Normalizes by sum(max_possible_per_hit) to produce a 0..1 score.
    """
    raw = 0.0
    tech_matches = 0

    # compute denominator: sum of max possible for each hit (max similarity 1.0 * max rating * max depth)
    max_rating = max(RATING_MULTIPLIER.values())
    max_depth = max(DEPTH_MULTIPLIER.values())
    denom = 0.0
    for hit in candidate_hits:
        denom += (1.0 * max_rating * max_depth)

    if denom == 0:
        denom = 1.0

    # scoring contributions
    for hit in candidate_hits:
        sid = hit['skillId']
        lvl = hit['level']
        sim = float(hit['similarity'])
        # L3 exact match?
        if lvl == 3 and sid in user['skillIdSet']:
            rating = user['selected_map'][sid]['rating']
            raw += sim * RATING_MULTIPLIER.get(rating, 1.0) * DEPTH_MULTIPLIER[3]
        # L4 exact tech match?
        elif lvl == 4 and sid in user['techIdSet']:
            # find parent L3 rating (we need to find which L3 entry contains this L4)
            # user.selected_map stores l3 -> {'rating', 'l4Ids'}
            parent_l3 = None
            for l3id, ent in user['selected_map'].items():
                if sid in ent['l4Ids']:
                    parent_l3 = l3id
                    rating = ent['rating']
                    break
            if parent_l3 is None:
                # not found - skip
                continue
            raw += sim * RATING_MULTIPLIER.get(rating, 1.0) * DEPTH_MULTIPLIER[4]
            tech_matches += 1
        # else not matched by user - no contribution

    tech_bonus = min(tech_matches * TECH_BONUS_PER_MATCH, TECH_BONUS_CAP)
    raw += tech_bonus

    normalized = max(0.0, min(1.0, raw / denom))
    return {
        "raw": raw,
        "normalized": normalized,
        "tech_matches": tech_matches,
        "denom": denom
    }

# ---------- Top-level search function ----------
def search_users_by_nl_query(query_text: str,
                             s3, s3vectors, bedrock_runtime,
                             skillById: Dict[str,Any],
                             users_by_l3, users_by_l4) -> List[Dict[str,Any]]:
    # 1) embed query
    q_vec = embed_text_bedrock(bedrock_runtime, query_text, BEDROCK_EMBEDDING_MODEL_ID)

    # 2) query S3 Vectors index (get top skill hits)
    raw_hits = query_skill_vectors(s3vectors, VECTOR_BUCKET, VECTOR_INDEX, q_vec, top_k=TOP_K)

    # 3) transform into candidate L3/L4 hits (with similarity)
    candidate_hits = expand_hits_to_candidate_skills(raw_hits, skillById)

    # 4) collect candidate users
    candidate_users = set()
    for hit in candidate_hits:
        if hit['level'] == 3:
            for u in users_by_l3.get(hit['skillId'], []):
                candidate_users.add(id(u))  # use id for dedupe; we will map back
        elif hit['level'] == 4:
            for u in users_by_l4.get(hit['skillId'], []):
                candidate_users.add(id(u))
            # also include users who selected the parent L3 if metadata has parent
            parent = hit.get('parent_l3')
            if parent:
                for u in users_by_l3.get(parent, []):
                    candidate_users.add(id(u))

    # map ids back to user objects efficiently: build dict of all users present in indices
    # (assumes small data set; otherwise maintain central users list->id mapping)
    # For simplicity, build an id->user map from users_by_l3 and users_by_l4
    id_to_user = {}
    for lst in list(users_by_l3.values()) + list(users_by_l4.values()):
        for u in lst:
            id_to_user[id(u)] = u

    results = []
    for uid in candidate_users:
        user = id_to_user.get(uid)
        if not user:
            continue
        score_info = score_user_against_hits(user, candidate_hits)
        # prepare matched skill details for explainability:
        matched = []
        for hit in candidate_hits:
            sid = hit['skillId']
            lvl = hit['level']
            if (lvl == 3 and sid in user['skillIdSet']) or (lvl == 4 and sid in user['techIdSet']):
                # fetch rating if possible
                rating = None
                if lvl == 3:
                    rating = user['selected_map'][sid]['rating']
                else:
                    # find parent L3 and rating
                    for l3id, ent in user['selected_map'].items():
                        if sid in ent['l4Ids']:
                            rating = ent['rating']
                            break
                matched.append({
                    "skillId": sid,
                    "level": lvl,
                    "title": skillById.get(sid, {}).get('title', sid),
                    "rating": rating,
                    "similarity": hit['similarity']
                })
        results.append({
            "userEmail": user['userEmail'],
            "score": score_info['normalized'],
            "raw_score": score_info['raw'],
            "tech_matches": score_info['tech_matches'],
            "matched": matched
        })

    # sort descending
    results.sort(key=lambda r: r['score'], reverse=True)
    return results

# ---------- Example main flow ----------
if __name__ == "__main__":
    s3, s3vectors, bedrock_runtime = make_clients()
    print("Loading master skills...")
    master_list = load_skills_master(s3, APP_BUCKET, SKILLS_MASTER_KEY)
    skill_by_id = flatten_skills_tree(master_list)

    print("Loading users into memory...")
    users, users_by_l3, users_by_l4 = load_users(s3, APP_BUCKET, USERS_PREFIX, skill_by_id)

    query = "Looking for an expert in AWS Lambda and serverless architecture"
    print(f"Searching for: {query}")
    results = search_users_by_nl_query(query, s3, s3vectors, bedrock_runtime, skill_by_id, users_by_l3, users_by_l4)

    print("Top results:")
    for r in results[:10]:
        print(f"- {r['userEmail']}: score={r['score']:.3f}, matched={[(m['title'], m['rating']) for m in r['matched']]}")
