"""Quick V2 inference test."""
import urllib.request
import json
import io

test_img = r'd:\ProjectsGit\Atelier\PersonalFashionStylistV2\datasets\fashion_products\images\15970.jpg'

# Build multipart form
boundary = 'boundary123456'
body = io.BytesIO()
# image field
body.write(f'--{boundary}\r\n'.encode())
body.write(f'Content-Disposition: form-data; name="image"; filename="test.jpg"\r\n'.encode())
body.write(b'Content-Type: image/jpeg\r\n\r\n')
with open(test_img, 'rb') as f:
    body.write(f.read())
body.write(b'\r\n')
# occasion_text field
body.write(f'--{boundary}\r\n'.encode())
body.write(b'Content-Disposition: form-data; name="occasion_text"\r\n\r\n')
body.write(b'casual\r\n')
body.write(f'--{boundary}--\r\n'.encode())
data = body.getvalue()

req = urllib.request.Request(
    'http://localhost:8000/api/style/item',
    data=data,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
)
r = urllib.request.urlopen(req, timeout=120)
result = json.loads(r.read())
print('=== Predictions ===')
print(json.dumps(result.get('predictions', {}), indent=2))
print('=== Direction ===')
print(result.get('direction'))
print('=== Explanation ===')
print(result.get('explanation'))
print('=== First 3 Recs ===')
for rec in result.get('recommendations', [])[:3]:
    print(f"  {rec['label']} score={rec['score']} sim={rec.get('similarity_score', 'N/A')} src={rec.get('source', 'N/A')}")
    print(f"    image_url={rec.get('image_url', 'N/A')}")
print(f"\nTotal recs: {len(result.get('recommendations', []))}")
