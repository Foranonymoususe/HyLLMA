import torch
from angle_emb import AnglE, Prompts
from datasets import load_dataset
from sklearn import svm
from sklearn.metrics import classification_report, roc_auc_score
from huggingface_hub import HfApi, HfFolder
import numpy as np
from sklearn.decomposition import PCA
import joblib
from sklearn.metrics import accuracy_score

angle = AnglE.from_pretrained('NousResearch/Llama-2-7b-hf',
                              pretrained_lora_path='',
                              pooling_strategy='last',
                              is_llm=True,
                              torch_dtype=torch.float16)  

dataset = load_dataset("")


def encode_traffic_data(item):
    input_text = item['input']
    completion_data = item['completion']
    return {
        'text': input_text + completion_data 
    }

doc_vecs = []

for item in dataset['train']:
    encoded = angle.encode([encode_traffic_data(item)], prompt=Prompts.A)
    doc_vecs.append(encoded[0]) 

X = np.array(doc_vecs)


print("Total embeddings:", X.shape) 
print(X)  

pca = PCA(n_components=1000)
X_reduced = pca.fit_transform(X)
joblib.dump(pca, 'pca_linear_1000.pkl')

svm_model = svm.OneClassSVM(nu=0.01, kernel='linear')
svm_model.fit(X_reduced)


hf_token = ""
api = HfApi()


model_path = "./one_class_svm_model_rbf.pkl"
with open(model_path, 'wb') as f:
    torch.save(svm_model, f)


repo_id = ""
api.create_repo(repo_id, token=hf_token, exist_ok=True)

api.upload_file(
    path_or_fileobj=model_path,
    path_in_repo="one_class_svm_model_rbf.pkl",
    repo_id=repo_id,
    token=hf_token
)
print("SVM 模型已成功上传到 Huggingface！")



pca_path = "./pca_linear_1000.pkl"
joblib.dump(pca, pca_path)
print(f"PCA 对象已保存到 {pca_path}")

api.upload_file(
    path_or_fileobj=pca_path,
    path_in_repo="pca_linear_1000.pkl",
    repo_id=repo_id,
    token=hf_token
)

