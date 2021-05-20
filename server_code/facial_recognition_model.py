import os
from PIL import Image
import numpy as np
from facenet_pytorch import MTCNN,InceptionResnetV1
import torch
import torch.nn as nn
from torchvision import transforms
from torchvision.datasets import ImageFolder
from torch.utils.data import DataLoader

import base64

def initial_model(device):
    resnet = InceptionResnetV1(pretrained='casia-webface').eval()
    mtcnn = MTCNN(thresholds=[.55, .55, .55],device=device)
    resnet.to(device)
    return resnet,mtcnn

def construct_dataloader(mtcnn,dataset_path,batch_size):
    tfm = transforms.Compose([
        transforms.Lambda(lambda x:mtcnn(x))
    ])
    dataset = ImageFolder(dataset_path,transform=tfm)
    dataloader = DataLoader(dataset,batch_size=batch_size)

    names = list(dataset.class_to_idx.keys())
    classes = list(dataset.class_to_idx.values())
    class_to_name = dict(zip(classes,names))
    return dataloader,class_to_name

def retrieve_embeddings(model,mtcnn,dataloader,device):
    embeddings = torch.tensor([])
    classes = torch.tensor([],dtype=torch.int)
    for data in dataloader:
        faces,class_label = data
        embedding = model(faces.to(device))
        embeddings = torch.cat([embeddings,embedding.cpu()],dim=0)
        classes = torch.cat([classes,class_label],dim=0)
    return embeddings,classes

def get_vector_length(vector):
    return np.sqrt(sum(np.square(vector)))

def compute_cosine_similarity(model,mtcnn,dataloader,device,query_embedding,class_to_name):
    doc_embeddings,classes = retrieve_embeddings(model,mtcnn,dataloader,device)
    similarity_dict = {}
    dist_list = []
    for doc_embedding,class_label in zip(doc_embeddings,classes):
        dot_product = np.dot(query_embedding.detach().cpu(),doc_embedding.detach().cpu())
        query_emb_length = get_vector_length(query_embedding.detach().cpu())
        doc_emb_length = get_vector_length(doc_embedding.detach().cpu())
        cosine_similarity = dot_product / (query_emb_length*doc_emb_length)
        similarity_dict[class_to_name[class_label.item()]] = (int)(round(cosine_similarity.item()*100,0))
        
        dist = sum(((query_embedding.detach().cpu() - doc_embedding.detach().cpu())**2).reshape(512))
        dist_list.append(dist)
        print(dist,class_to_name[class_label.item()])
    return similarity_dict

def sort_dict(dict_to_sort):
    sorted_similarity = sorted(dict_to_sort.items(), key = lambda x:x[1])
    sorted_similarity.reverse()
    sorted_similarity = dict(sorted_similarity)
    return sorted_similarity

def get_picture(top_n,dataset_path):
#     picture_list = []
    file_name_list = []
    for top_information in top_n:
        star_name = top_information[0]
        folder_path = os.path.join(dataset_path,star_name)
        for _, _, file_names in os.walk(folder_path):
            file_name_list.append(file_names[0])
#             print(folder_path,file_names)
#             file_path = os.path.join(folder_path,file_names[0])
            
#             with open(file_path,'rb') as img:
#                 image = base64.b64encode(img.read()).decode('latin1')
#                 picture_list.append(image)
            break
#     return picture_list
    return file_name_list

def similarity_recognition(query_image,dataset_path,top_n=1):    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model,mtcnn = initial_model(device)

    #convert query_image to embedding
    query_face = mtcnn(query_image)
    query_embedding = model(query_face.unsqueeze(0).to(device))[0]

    dataloader,class_to_name = construct_dataloader(mtcnn,dataset_path,batch_size=8)
    similarity_dict = compute_cosine_similarity(model,mtcnn,dataloader,device,query_embedding,class_to_name)
    similarity_dict = sort_dict(similarity_dict)
    top_n = list(similarity_dict.items())[:top_n]
    top_n_name_list = get_picture(top_n,dataset_path)
    response = {'similarity':top_n, 'names':top_n_name_list}
    return response