import torch
from torchvision import datasets, models, transforms
import json
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import time

import numpy as np
import matplotlib.pyplot as plt
import os

image_transforms = {
    'train': transforms.Compose([
        transforms.RandomResizedCrop(size=256, scale=(0.8, 1.0)),
        transforms.RandomRotation(degrees=15),
        transforms.RandomHorizontalFlip(),
        transforms.CenterCrop(size=224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225])
    ]),
    'valid': transforms.Compose([
        transforms.Resize(size=256),
        transforms.CenterCrop(size=224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225])
    ])

}


img_path="../Violent/"
batch_size=32
train_dataset=datasets.ImageFolder(root=img_path + 'train',transform=image_transforms['train'])

train_loder=DataLoader(train_dataset,batch_size=batch_size,shuffle=True)
val_dataset=datasets.ImageFolder(root=img_path+'val',transform=image_transforms['valid'])
val_loder=DataLoader(val_dataset,batch_size=batch_size,shuffle=True)
train_size=len(train_dataset)
val_size=len(val_dataset)
print(train_size,val_size)

print(train_dataset.class_to_idx)


train_num = len(train_dataset)

violent_list=train_dataset.class_to_idx
cla_dict = dict((val, key) for key, val in violent_list.items())   # 把花和数字的值反一下
# write dict into json file  搞一个json文件
json_str = json.dumps(cla_dict, indent=4)
with open('class_indices.json', 'w') as json_file:
    json_file.write(json_str)

# batch_size=32
# train_dataset=np.expand_dims(train_dataset,0)
resnet50=models.resnet50(pretrained=True)

for param in resnet50.parameters():
    param.requires_grad = False
fc_inputs = resnet50.fc.in_features
resnet50.fc = nn.Sequential(
    nn.Linear(fc_inputs, 256),
    nn.ReLU(),
    nn.Dropout(0.4),
    nn.Linear(256, 2),
    nn.LogSoftmax(dim=1)
)
# resnet50 = resnet50.to('cuda:0')

loss_func = nn.NLLLoss()
optimizer = optim.Adam(resnet50.parameters())


def train_and_valid(model, loss_function, optimizer, epochs=25):
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    history = []
    best_acc = 0.0
    best_epoch = 0

    for epoch in range(epochs):
        epoch_start = time.time()
        print("Epoch: {}/{}".format(epoch + 1, epochs))

        model.train()

        train_loss = 0.0
        train_acc = 0.0
        valid_loss = 0.0
        valid_acc = 0.0

        for i, (inputs, labels) in enumerate(train_loder):
            # inputs = inputs.to(device)
            # labels = labels.to(device)

            # 因为这里梯度是累加的，所以每次记得清零
            optimizer.zero_grad()

            outputs = model(inputs)

            loss = loss_function(outputs, labels)

            loss.backward()

            optimizer.step()

            train_loss += loss.item() * inputs.size(0)

            ret, predictions = torch.max(outputs.data, 1)
            correct_counts = predictions.eq(labels.data.view_as(predictions))

            acc = torch.mean(correct_counts.type(torch.FloatTensor))

            train_acc += acc.item() * inputs.size(0)

        with torch.no_grad():
            model.eval()

            for j, (inputs, labels) in enumerate(val_loder):
                # inputs = inputs.to(device)
                # labels = labels.to(device)

                outputs = model(inputs)

                loss = loss_function(outputs, labels)

                valid_loss += loss.item() * inputs.size(0)

                ret, predictions = torch.max(outputs.data, 1)
                correct_counts = predictions.eq(labels.data.view_as(predictions))

                acc = torch.mean(correct_counts.type(torch.FloatTensor))

                valid_acc += acc.item() * inputs.size(0)

        avg_train_loss = train_loss / train_size
        avg_train_acc = train_acc / train_size

        avg_valid_loss = valid_loss / val_size
        avg_valid_acc = valid_acc / val_size

        history.append([avg_train_loss, avg_valid_loss, avg_train_acc, avg_valid_acc])

        if best_acc < avg_valid_acc:
            best_acc = avg_valid_acc
            best_epoch = epoch + 1

        epoch_end = time.time()

        print(
            "Epoch: {:03d}, Training: Loss: {:.4f}, Accuracy: {:.4f}%, \n\t\tValidation: Loss: {:.4f}, Accuracy: {:.4f}%, Time: {:.4f}s".format(
                epoch + 1, avg_train_loss, avg_train_acc * 100, avg_valid_loss, avg_valid_acc * 100,
                epoch_end - epoch_start
            ))
        print("Best Accuracy for validation : {:.4f} at epoch {:03d}".format(best_acc, best_epoch))

        torch.save(model, 'models/' + '_model_' + str(epoch + 1) + '.pt')
    return model, history


num_epochs = 30
trained_model, history = train_and_valid(resnet50, loss_func, optimizer, num_epochs)
torch.save(history, 'models/'  + '_history.pt')

history = np.array(history)
plt.plot(history[:, 0:2])
plt.legend(['Tr Loss', 'Val Loss'])
plt.xlabel('Epoch Number')
plt.ylabel('Loss')
plt.ylim(0, 1)
plt.savefig('models/' + '_loss_curve.png')
plt.show()

plt.plot(history[:, 2:4])
plt.legend(['Tr Accuracy', 'Val Accuracy'])
plt.xlabel('Epoch Number')
plt.ylabel('Accuracy')
plt.ylim(0, 1)
plt.savefig('models/'  + '_accuracy_curve.png')
plt.show()





# dataset = 'animals-10'
# train_directory = os.path.join(dataset, 'train')
# valid_directory = os.path.join(dataset, 'valid')
#
# batch_size = 32
# num_classes = 10
#
# data = {
#     'train': datasets.ImageFolder(root=train_directory, transform=image_transforms['train']),
#     'valid': datasets.ImageFolder(root=valid_directory, transform=image_transforms['valid'])
#
# }
#
# train_data_size = len(data['train'])
# valid_data_size = len(data['valid'])
#
# train_data = DataLoader(data['train'], batch_size=batch_size, shuffle=True)
# valid_data = DataLoader(data['valid'], batch_size=batch_size, shuffle=True)
#
# print(train_data_size, valid_data_size)
