from deepface import DeepFace

result = DeepFace.verify(img1_path="1.jpg", img2_path="2.jpg", model_name="ArcFace")
print(result["verified"])  # True yoki False
print(result["distance"])  # Farq, 0.0 - 1.0 oralig‘ida