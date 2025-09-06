import aiohttp
import hashlib
import numpy as np
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from motor.motor_asyncio import AsyncIOMotorDatabase
from redis.asyncio import Redis
from server.utils.custom_logging import get_logger
from typing import List

logger = get_logger(__name__)

async def recommend_careers(interests: str, db:AsyncIOMotorDatabase, redis: Redis) -> List[dict]:
    cache_key = f"careers:{hashlib.md5(interests.encode()).hexdigest()}"
    cached = await redis.get(cache_key)
    if cached:
        logger.info(f"Cache hit for interests: {interests}")
        return eval(cached)
    
    # Fetch careers
    careers = await db.careers.find().to_list(100)
    if not careers:
        async with aiohttp.ClientSession() as session:
            for attempt in range(3):
                try:
                    async with session.get("https://services.onetcenter.org/ws/online/occupations") as response:
                        if response.status != 200:
                            raise Exception(f"O*NET API failed: {response.status}")
                        onet_data = await response.json()
                        careers = [
                            {"title": job["title"], "description": job["description"], "skills": job["skills"], "industry": job["industry"], "vector": []}
                            for job in onet_data["occupations"]
                        ]
                        break
                except Exception as e:
                    logger.warning(f"O*NET retry {attempt + 1}/3: {str(e)}")
                    if attempt == 2:
                        raise Exception("Failed to fetch career data")
        await db.careers.insert_many(careers)
        logger.info("Populated MongoDB with O*NET data")

    # TF-IDF and clustering
    try:
        vectorizer = TfidfVectorizer(stop_words = "english")
        career_texts = [c["description"] for c in careers]
        vectors = vectorizer.fit_transform([interests] + career_texts).toarray()
        kmeans = KMeans(n_clusters = 5, random_state = 42)
        clusters = kmeans.fit_predict(vectors[1:])
        similarities = np.dot(vectors[0], vectors[1:].T)
        top_indicies = similarities.argsort()[-5:][::-1]
        result = [careers[i] for i in top_indicies]

        # Update vectors for FAISS
        index = faiss.IndexFlatL2(vectors.shape[1])
        index.add(vectors[1:].astype(np.float32))
        for i, career in enumerate(careers):
            career["vector"] = vectors[i + 1].tolist()
            await db.careers.update_one({"title": career["title"]}, {"$set": {"vector": career["vector"]}})
    except Exception as e:
        logger.error(f"Error in career recommendation: {str(e)}")
        raise Exception("Failed to generate recommendations")
    
    # Cache results
    await redis.setex(cache_key, 3600, str(result))
    logger.info(f"Cache set for interests: {interests}")
    return result