# The MNIST database of handwritten digits. http://yann.lecun.com/exdb/mnist/
#
# In this problem you need to implement model that will learn to recognize
# handwritten digits
import time
import random
import torch
import torchvision
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
from ..utils.gridsearch import GridSearch
from ..utils import solutionmanager as sm


class SolutionModel(nn.Module):
    def __init__(self, input_size, output_size, solution):
        super(SolutionModel, self).__init__()
        self.input_size = input_size
        self.output_size = output_size
        self.lr = solution.lr
        self.momentum = solution.momentum
        self.activation = solution.activation
        self.activations = solution.activations
        self.fc1 = nn.Linear(input_size, 500)
        self.fc2 = nn.Linear(500, 256)
        self.fc3 = nn.Linear(256, output_size)

    def forward(self, x):
        x = x.view(-1, self.input_size)
        x = self.activations[self.activation](self.fc1(x))
        x = self.activations[self.activation](self.fc2(x))
        x = self.fc3(x)
        return F.log_softmax(x, dim=1)

    def calc_loss(self, output, target):
        loss = F.nll_loss(output, target)
        return loss

    def calc_predict(self, output):
        predict = output.max(1, keepdim=True)[1]
        return predict


class Solution():
    def __init__(self):
        self.lr = .1
        self.momentum = 0.9
        self.momentum_grid = list(np.linspace(0.5, 1, 10))
        self.lr_grid = list(np.linspace(0.01, 0.05, 10))
        self.activations = {
            'relu6': nn.ReLU6(),
            'leakyrelu': nn.LeakyReLU(negative_slope=0.01),
            'relu': nn.ReLU(),
        }
        self.activation = 'relu6'
        self.activation_grid = list(self.activations.keys())
        self.grid_search = GridSearch(self)
        self.grid_search.set_enabled(True)

    def create_model(self, input_size, output_size):
        return SolutionModel(input_size, output_size, self)

    # Return number of steps used
    def train_model(self, model, train_data, train_target, context):
        step = 0
        # Put model in train mode
        model.train()
        optimizer = optim.SGD(model.parameters(), model.lr, model.momentum)
        while True:
            time_left = context.get_timer().get_time_left()
            # No more time left, stop training
            # if time_left < 0.1:
            #     break
            data = train_data
            target = train_target
            # model.parameters()...gradient set to zero
            optimizer.zero_grad()
            # evaluate model => model.forward(data)
            output = model(data)
            # get the index of the max probability
            predict = model.calc_predict(output)
            # Number of correct predictions
            correct = predict.eq(target.view_as(predict)).long().sum().item()
            # Total number of needed predictions
            total = predict.view(-1).size(0)
            # calculate loss
            loss = model.calc_loss(output, target)

            if correct == total or time_left < 0.1:
                stats = {
                    'step': step,
                    'loss': round(loss.item(), 5),
                    'lr': self.lr,
                    'activ': self.activation,
                    'moment': getattr(self, 'momentum', 0)
                }
                if self.grid_search.enabled:
                    results.append(stats)
                break

            # calculate deriviative of model.forward() and put it in model.parameters()...gradient
            loss.backward()
            # print progress of the learning
            # update model: model.parameters() -= lr * gradient
            optimizer.step()
            step += 1
        return step

    def print_stats(self, step, loss, correct, total):
        if step % 100 == 0:
            print("Step = {} Prediction = {}/{} Error = {}".format(step,
                                                                   correct, total, loss.item()))

###
###
# Don't change code after this line
###
###


class Limits:
    def __init__(self):
        self.time_limit = 2.0
        self.size_limit = 1000000
        self.test_limit = 0.95


class DataProvider:
    def __init__(self):
        self.number_of_cases = 10
        print("Start data loading...")
        train_dataset = torchvision.datasets.MNIST(
            './data/data_mnist', train=True, download=True,
            transform=torchvision.transforms.ToTensor()
        )
        trainLoader = torch.utils.data.DataLoader(
            train_dataset, batch_size=len(train_dataset))
        test_dataset = torchvision.datasets.MNIST(
            './data/data_mnist', train=False, download=True,
            transform=torchvision.transforms.ToTensor()
        )
        test_loader = torch.utils.data.DataLoader(
            test_dataset, batch_size=len(test_dataset))
        self.train_data = next(iter(trainLoader))
        self.test_data = next(iter(test_loader))
        print("Data loaded")

    def select_data(self, data, digits):
        data, target = data
        mask = target == -1
        for digit in digits:
            mask |= target == digit
        indices = torch.arange(0, mask.size(0))[mask].long()
        return (torch.index_select(data, dim=0, index=indices), target[mask])

    def create_case_data(self, case):
        if case == 1:
            digits = [0, 1]
        elif case == 2:
            digits = [8, 9]
        else:
            digits = [i for i in range(10)]

        description = "Digits: "
        for ind, i in enumerate(digits):
            if ind > 0:
                description += ","
            description += str(i)
        train_data = self.select_data(self.train_data, digits)
        test_data = self.select_data(self.test_data, digits)
        return sm.CaseData(case, Limits(), train_data, test_data).set_description(description).set_output_size(10)


class Config:
    def __init__(self):
        self.max_samples = 1000

    def get_data_provider(self):
        return DataProvider()

    def get_solution(self):
        return Solution()


# If you want to run specific case, put number here
results = []
sm.SolutionManager(Config()).run(case_number=1)

if results:
    with open('results.txt', 'w') as f:
        text = ',\n'.join(str(i) for i in sorted(
            results, key=operator.itemgetter('step')))
        f.write(text)
