from facenet_pytorch import MTCNN,InceptionResnetV1
import torch
import torch.nn as nn

class Model(nn.Module):
    def __init__(self,resnet):
        super(Model,self).__init__()
        
        self.net = nn.Sequential(
            resnet,
            nn.Linear(512,3)
        )
        
    def forward(self,x):
        return self.net(x)
    
def initial_model(device):
    resnet = InceptionResnetV1(pretrained='casia-webface').eval()
    model = Model(resnet)
    model.load_state_dict(torch.load('models/facenet',map_location='cpu'))
    model.to(device)
    mtcnn = MTCNN(thresholds=[.55, .55, .55],device=device)
    return model,mtcnn

def emotion_recognition(PILimage,print_prob=False):
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model,mtcnn = initial_model(device)
    embedding = mtcnn(PILimage) #shape = [3,128,128] (C,H,W)
    embeddings = embedding.unsqueeze(0) #shape = [1,3,128,128] (B,C,H,W)
    logits = model(embeddings.to(device))
    max_logit,target_class = torch.max(logits,dim=1)
    softmax = nn.Softmax(dim=1)
    probs = softmax(logits)
    class_dict = {0:'正常',1:'開心',2:'生氣'}
    if print_prob:
        print(list(probs.cpu().detach().numpy()[0]))
    return {'emotion':class_dict[target_class.item()]}