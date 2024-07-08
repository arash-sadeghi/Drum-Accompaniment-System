import torch.nn as nn
import torch.nn.functional as F

# from CONST_VARS import CONST
from models.CONST_VARS import CONST

import torch
class GeneraterBlock(nn.Module):
    def __init__(self, in_dim, out_dim, kernel, stride ,output_padding = 0):
        super().__init__()
        self.transconv = nn.ConvTranspose3d(in_dim, out_dim, kernel, stride ,output_padding = output_padding)
        self.batchnorm = nn.BatchNorm3d(out_dim)

    def forward(self, x):
        x = self.transconv(x)
        x = self.batchnorm(x) 
        return F.relu(x)

class ConditionerBlock(nn.Module):
    def __init__(self, in_dim, out_dim, kernel, stride):
        super().__init__()
        self.conv = nn.Conv3d(in_dim, out_dim, kernel, stride) 
        self.batchnorm = nn.BatchNorm3d(out_dim)


    def forward(self, x):
        x = self.conv(x)
        x = self.batchnorm(x)
        # return F.relu(x)
        return F.leaky_relu(x)

class Generator(nn.Module):
    latent_depth_chanel = 3*CONST.latent_dim
    def __init__(self):
        super().__init__() #! layer norms are adjusted as such to generate an ouput of lenght 64x72

        embedding_size = CONST.latent_dim
        num_embeddings = len(CONST.genre_code)  
        self.embedder = nn.Embedding(num_embeddings, embedding_size)
        
        self.conv0 = ConditionerBlock(1, 16, (1, 1, 12), (1, 1, 12))
        self.conv1 = ConditionerBlock(16, 32, (1, 4, 1), (1, 4, 1))
        self.conv2 = ConditionerBlock(32, 64, (1, 1, 3), (1, 1, 1))
        self.conv3 = ConditionerBlock(64, 128, (1, 1, 4), (1, 1, 4))
        self.conv4 = ConditionerBlock(128, 256, (1, 4, 1), (1, 4, 1))
        self.conv5 = ConditionerBlock(256 , CONST.latent_dim , (4, 1, 1), (4, 1, 1))

        self.transconv0 = GeneraterBlock(Generator.latent_depth_chanel, 256, (4, 1, 1), (4, 1, 1))
        self.transconv1 = GeneraterBlock(256, 128, (1, 4, 1), (1, 4, 1))
        self.transconv2 = GeneraterBlock(128, 64, (1, 1, 4), (1, 1, 4))
        self.transconv3 = GeneraterBlock(64, 32, (1, 1, 3), (1, 1, 1))
        self.transconv4 = GeneraterBlock(32, 16, (1, 4, 1), (1, 4, 1))
        self.transconv5 = GeneraterBlock(16, 1, (1, 1, 12), (1, 1, 12))


    def forward(self, x , condition , genre): #! torch.Size([1, 128])

        condition = condition.view(-1,1, CONST.n_measures , CONST.measure_resolution, CONST.n_pitches) 
        # x = x.view(CONST.BATCH_SIZE ,1, CONST.n_measures , CONST.measure_resolution, CONST.n_pitches) 
        condition = self.conv0(condition) 
        condition = self.conv1(condition)
        condition = self.conv2(condition)
        condition = self.conv3(condition) 
        condition = self.conv4(condition)
        condition = self.conv5(condition)
        condition = condition.view(-1, CONST.latent_dim)        
        
        genre = self.embedder(genre)
        x = torch.cat((x, condition,genre),axis=1)

        # layer = 0
        x = x.view(-1, Generator.latent_depth_chanel, 1, 1, 1) #! torch.Size([1, 128, 1, 1])
        # print(f"layer {layer} size {x.shape}");layer+=1        

        x = self.transconv0(x) #! torch.Size([1, 128, 4, 4]) #! torch.Size([1, 128, 3, 3])
        # print(f"layer {layer} size {x.shape}");layer+=1        

        x = self.transconv1(x) #! torch.Size([1, 64, 10, 10]) #! torch.Size([1, 64, 7, 7])
        # print(f"layer {layer} size {x.shape}");layer+=1        

        x = self.transconv2(x) #! torch.Size([1, 32, 22, 22]) #! torch.Size([1, 32, 15, 15])
        # print(f"layer {layer} size {x.shape}");layer+=1        

        x = self.transconv3(x) #! torch.Size([1, 16, 46, 46]) #! torch.Size([1, 16, 31, 31])
        # print(f"layer {layer} size {x.shape}");layer+=1        

        x = self.transconv4(x) #! torch.Size([1, 1, 94, 94]) #! torch.Size([1, 1, 63, 63])
        # print(f"layer {layer} size {x.shape}");layer+=1        

        x = self.transconv5(x) #! torch.Size([1, 1, 94, 94]) #! torch.Size([1, 1, 63, 63])
        # print(f"layer {layer} size {x.shape}");layer+=1        


        x = x.view(-1, 1, CONST.n_measures * CONST.measure_resolution, CONST.n_pitches)
        return x
