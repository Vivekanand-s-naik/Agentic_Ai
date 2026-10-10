from rank_bm25 import BM25Plus  


documents = [
    "Python is a programming language",
    "Python is used for machine learning and artificial intelligence",
    "Java is commonly used for backend development",
    "React is used for frontend development"
]

query = "intelligence"


# Tokenize documents
tokenized_documents = [
    document.lower().split()
    for document in documents
]


# Create BM25 index
bm25 = BM25Plus(tokenized_documents)


# Tokenize query
tokenized_query = query.lower().split()


# Get scores
scores = bm25.get_scores(tokenized_query)
print(scores)

# Rank documents
ranked = sorted(
    enumerate(scores),
    key=lambda x: x[1],
    reverse=True
)

print(ranked)
for index, score in ranked:
    print(f"Score: {score:.4f} | {documents[index]}")