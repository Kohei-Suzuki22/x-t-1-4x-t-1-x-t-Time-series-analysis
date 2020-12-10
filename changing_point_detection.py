import numpy as np
import matplotlib.pyplot as plt
from matplotlib import mathtext
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle
from sklearn.metrics import mean_squared_error
import torch
import torch.nn as nn
import torch.optim as optimizers
import ipdb
import os
mathtext.FontConstantsBase = mathtext.ComputerModernFontConstants

# ipdb.set_trace()
# plt.rcParams["font.size"] = 10
# fig = plt.figure(figsize=(20.0,12.0/0.96))


class RNN_parent(nn.Module):
    def __init__(self,hidden_dim,bidirectional):
        super().__init__()
        if bidirectional == True:
            self.l2 = nn.Linear(hidden_dim*2, 1)
        elif bidirectional == False:
            self.l2 = nn.Linear(hidden_dim, 1)


    def initialize_weight(self):
       # ザビエル正規分布(ノード数nに対して平均0・標準偏差1/√n)を用いた重みの初期化 → ランダムではなく学習に最適な重みを設定
        # 標準偏差 * gainで初期化を行う
        # gainは基本的に5/3にすることが多い → 層が増えたときに安定しやすいと言われている。
        nn.init.xavier_normal_(self.l1.weight_ih_l0,gain=5/3)       # weight_ih: 入力層 → 隠れ層 に対する重みの初期化

        # 直行行列を用いた重みの初期化(通常の重みの初期化手法を用いるとRNNではオーバーフローを発生させる可能性が高い)
        # weight_hh: 隠れ層 → 隠れ層    に対する重みの初期化    ※ 隠れ層 → 出力層 の場合 hoがないみたいなので、hhで良い。
        # l0: 隠れ層1層目の重みの初期化
        # l1: 隠れ層2層目の重みの初期化
        # l2' 隠れ層3層目の重みの初期化
        for layer in range(num_layers):
            # それぞれの隠れ層の重みを初期化
            nn.init.orthogonal_(eval("self.l1.weight_hh_l{}".format(layer)),gain=5/3)   # tanhの場合はgain=5/3 が理想


    def forward(self, x,batch_size,affect_length):
        x = x.reshape(batch_size,-1,affect_length)
        for layer in self.layers:
            if type(layer(x)) == tuple:
                x = layer(x)[0]
            else:
                x = layer(x)

        return x



class RNN(RNN_parent):
    def __init__(self,input_dim,hidden_dim,num_layers=1,activation='tanh',bidirectional=False):
        RNN_parent.__init__(self,hidden_dim,bidirectional)
            # 各パラメータ設定: nn.RNN(input_size,hidden_size,num_layers=1,nonlinearity='tanh',bias=True,batch_first=False,dropout=0,bidirectional=False)
            # 活性化関数(nonlinearity)は tanh・relu のどちらかのみ。
        self.l1 = nn.RNN(input_dim, hidden_dim,num_layers=num_layers,nonlinearity=activation,batch_first=True,bidirectional=bidirectional)
        RNN_parent.initialize_weight(self)

        self.layers = [self.l1,self.l2]


class LSTM(RNN_parent):
    def __init__(self,input_dim,hidden_dim,num_layers=1,bidirectional=False):
        RNN_parent.__init__(self,hidden_dim,bidirectional)
        self.l1 = nn.LSTM(input_dim, hidden_dim,num_layers=num_layers,batch_first=True,bidirectional=bidirectional)
        RNN_parent.initialize_weight(self)

        self.layers = [self.l1,self.l2]


class GRU(RNN_parent):
    def __init__(self,input_dim,hidden_dim,num_layers=1,bidirectional=False):
        RNN_parent.__init__(self,hidden_dim,bidirectional)
        self.l1 = nn.GRU(input_dim, hidden_dim,num_layers=num_layers,batch_first=True,bidirectional=bidirectional)
        RNN_parent.initialize_weight(self)

        self.layers = [self.l1,self.l2]


class MLP(nn.Module):
    def __init__(self, input_dim, hidden_dim,num_layers=1):
        super().__init__()
        self.l1 = nn.Linear(input_dim,hidden_dim)
        self.a1 = nn.Tanh()
        self.l2 = nn.Linear(hidden_dim,1)

        self.layers = [self.l1, self.a1, self.l2]

    def forward(self, x,batch_size,affect_length):
        x = x.reshape(batch_size,-1,affect_length)
        for layer in self.layers:
            if isinstance(layer,torch.nn.modules.rnn.GRU):
                x = layer(x)[0]
            else:
                x = layer(x)

        return x


class LogisticFunc():

    def __init__(self,before_a,after_a):
        self.before_a = before_a
        self.after_a = after_a
        self.x = np.array([0.2])

    def logistic_func(self,t,a):
            return a * self.x[t] * (1 - self.x[t])

    def make_time_series(self):
        for t in range(500+(affect_length-1)):
            if t < 250:
                self.x = np.append(self.x,self.logistic_func(t,self.before_a))
            else:
                self.x = np.append(self.x,self.logistic_func(t,self.after_a))
        return self.x

class HenonFunc():

    def __init__(self,b,before_a,after_a):
        self.b = 0.3
        self.before_a = before_a
        self.after_a = after_a
        self.x = np.array([0.1])
        self.y = np.array([0.])

    def henon_func_x(self,t,a):
        return 1 - a * self.x[t] ** 2 + self.y[t]

    def henon_func_y(self,t,a):
        return self.b * self.x[t]

    def make_time_series(self):
        for t in range(500+(affect_length-1)):
            if t < 250:
                self.x = np.append(self.x,self.henon_func_x(t,self.before_a))
                self.y = np.append(self.y,self.henon_func_y(t,self.before_a))
            else:
                self.x = np.append(self.x,self.henon_func_x(t,self.after_a))
                self.y = np.append(self.y,self.henon_func_y(t,self.after_a))

        return self.x




def factors_answers_init():
    factors = np.array([])
    answers = np.array([])
    return (factors,answers)

def set_factors_answers(x,factors,answers,affect_length,batch_size):
    for i in range(len(x) - affect_length):
        factors = np.append(factors,x[i:i+affect_length])
        answers = np.append(answers,x[i+affect_length])
    factors = factors.reshape(-1,affect_length,1)
    answers = answers.reshape(-1,1)         # .shape: (500,1)
    return (factors,answers)

def make_dataset(target,affect_length,batch_size,before_a,after_a):
    factors,answers = factors_answers_init()
    if target == "logistic":
        func = LogisticFunc(before_a,after_a)
    elif target == "henon":
        func = HenonFunc(0.3,before_a,after_a)
    x = func.make_time_series()
    factors,answers = set_factors_answers(x,factors,answers,affect_length,batch_size)
    return (x,factors,answers)


# 誤差を計算(平均二乗誤差).
def compute_loss(preds,answers,criterion):
    return criterion(preds, answers)

# 学習ステップ
def train_step(factors,answers,model,criterion,optimizer,batch_size,affect_length):
    # factors,answersを pytorch用データに変換。
    factors = torch.Tensor(factors).to(device)
    answers = torch.Tensor(answers).to(device)
    model.train()                       # モデルに「学習モードになれ」と伝える。
    preds = model(factors,batch_size,affect_length)              # forwardメソッド実行。   # factors.shape: (num1,num2,num3)の３次元を入れる必要がある
    loss = compute_loss(preds,answers,criterion)  # 誤差は平均二乗誤差.
    optimizer.zero_grad()               # zero_gradがないと勾配が累積されていく。zero_gradで一回ごと勾配をクリア。
    loss.backward()                     # 誤差逆伝播.
    optimizer.step()                    # パラメータの更新.
    return loss, preds

# 学習実行 & 学習損失GET.
def get_loss(factors,answers,model,criterion,optimizer,batch_size,affect_length,epochs,before_a,after_a):
    n_batches = factors.shape[0] // batch_size
    hist = {'loss': []}
    min_train_loss  = np.Inf
    n_epochs_stop = 30
    epochs_no_improve = 0

    for epoch in range(epochs):
        train_loss = 0.
        loss_per_batch = np.array([])
        preds_per_batch = np.array([])
        for batch in range(n_batches):
            start = batch * batch_size
            end = start + batch_size
            loss, preds = train_step(factors[start:end], answers[start:end],model,criterion,optimizer,batch_size,affect_length)
            train_loss += loss.data
            loss_per_batch = np.append(loss_per_batch,loss.data)
            preds_per_batch = np.append(preds_per_batch,preds.data)
        train_loss /= n_batches
        train_loss = np.round(train_loss.numpy(),5)  #少数第6桁目を四捨五入. 5桁目まで表示

        if train_loss < min_train_loss:
            min_train_loss = train_loss
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1

        print('epoch: {}, loss: {:.5}'.format(epoch+1,train_loss))

        if (epoch > n_epochs_stop) and (epochs_no_improve >= n_epochs_stop):
            print("Early Stopping")
            epochs = epoch+1
            break
        else:
            print("epochs_no_improve = {}".format(epochs_no_improve))
            continue

    return (loss_per_batch,preds_per_batch,epochs)



# グラフの作成
class Show_graph():

    def __init__(self,x,before_a,after_a,answers,preds,loss_per_batch,epochs,affect_length):
        self.x = x
        self.before_a = before_a
        self.after_a = after_a
        self.answers = answers
        self.preds = preds
        self.loss_per_batch = loss_per_batch
        self.epochs = epochs
        self.affect_length = affect_length

    def show_raw(self):
        plt.subplot(1,1,1)
        plt.xlabel("t")
        plt.xticks([0,50,100,150,200,250,300,350,400,450,500])
        plt.ylabel("x(t)")
        plt.plot(range(len(self.x)), self.x, linewidth=1.0,color="blue",label="{0}~{1}".format(self.before_a,self.after_a))

    def show_compare_raw_preds(self):
        plt.subplot(3,1,1)
        plt.xlabel("t")
        plt.xticks([self.affect_length,50,100,150,200,250,300,350,400,450,500])
        plt.ylabel("x(t)")
        plt.plot(range(self.affect_length,len(self.answers)+self.affect_length), self.answers, linewidth=1,color="blue",label="row_data")
        plt.plot(range(self.affect_length,len(self.preds)+self.affect_length),self.preds,linewidth=0.6,color="red",label="pred")

    def show_loss_per_batch(self):
        plt.subplot(3,1,2)
        plt.plot(range(self.affect_length,len(self.loss_per_batch)+self.affect_length),self.loss_per_batch,color="blue",label="{0}~{1} (epochs={2})".format(self.before_a,self.after_a,self.epochs))
        plt.xlabel("t")
        plt.xticks([self.affect_length,50,100,150,200,250,300,350,400,450,500])
        plt.ylabel("E(t)")
        interval = 10
        end = self.loss_per_batch.shape[0]
        start = end // interval

    def show_move_mean_loss_per_batch(self,mean_range=10):
        plt.subplot(3,1,3)
        move_mean_value = self.take_move_mean(self.loss_per_batch,mean_range,"full")
        plt.plot(range(self.affect_length,len(move_mean_value)+self.affect_length),move_mean_value,color="blue",label="{0}~{1} (epochs={2})".format(self.before_a,self.after_a,self.epochs))
        plt.xlabel("t")
        plt.xticks([self.affect_length,50,100,150,200,250,300,350,400,450,500])
        plt.ylabel("E(t)")

    def take_move_mean(self,loss,filter_array,mode):
        mean_range = np.ones(filter_array) / filter_array
        move_mean_x = np.convolve(loss,mean_range,mode=mode)[:500]
        return move_mean_x


def execute_all(target,model,neuron_num,num_layers,activation,batch_size,affect_length,epochs,before_a,after_a,learning_rate=0.001):
    criterion = nn.MSELoss(reduction='mean')    # 損失関数: 平均二乗誤差
    optimizer = optimizers.Adam(model.parameters(), lr=learning_rate, betas=(0.9, 0.999), amsgrad=True)     # 最適化手法Adam
    x,factors,answers = make_dataset(target,affect_length,batch_size,before_a,after_a)
    loss_per_batch,preds_per_batch,epochs = get_loss(factors,answers,model,criterion,optimizer,batch_size,affect_length,epochs,before_a,after_a)
    # plt.rcParams["font.size"] = 37
    plt.rcParams["font.size"] = 24
    # fig = plt.figure(figsize=(20.0,12.0/0.96))
    # show_graph_raw(x,before_a,after_a)
    graph = Show_graph(x,before_a,after_a,answers,preds_per_batch,loss_per_batch,epochs,affect_length)
    graph.show_compare_raw_preds()
    graph.show_loss_per_batch()
    graph.show_move_mean_loss_per_batch()
    plt.tight_layout()

    dir_name = "{}/BRNN/learning_rate{}/affect_length{}/neuron{}/num_layers{}/activation_{}".format(target,learning_rate,affect_length,neuron_num,num_layers,activation)
    os.makedirs(dir_name,exist_ok=True)
    fig.savefig("{}/prediction_accuracy{}to{}_{}epochs.png".format(dir_name,before_a,after_a,epochs))
    # fig.savefig("test_dir/prediction_accuracy{}to{}_{}epochs.png".format(affect_length,before_a,after_a,epochs))
    # fig.savefig("{}/raw_data{}to{}_{}epochs.png".format(dir_name,before_a,after_a,epochs))
    # plt.show()

if __name__ == '__main__':
    np.random.seed(123)
    torch.manual_seed(123)
    # deviceに実行環境を格納することで同じコードをCPU,GPUどちらも対応.
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')   # 実行環境が CPU か GPU かを判別して適用。

    # affect_length = 10
    batch_size = 1
    epochs = 1000


    # params = [3.95,3.99,3.9,3.85,3.8,3.75,3.7]
    # params = [3.4]
    # params = [1.05,1.10,1.15,1.20,1.25,1.30,1.35,1.36,1.37,1.38,1.39]
    # params = [1.35,1.36,1.37,1.38,1.39,1.40]
    params = [1.35]

    # params = [1.00]
    # neuron_nums = [2,4,8,16]
    neuron_nums = [8]
    # num_layers_set = [1,3,5,7]
    # num_layers_set = [1,2,3]
    num_layers_set = [2]
    # affect_length_set = [1,2,3,4,5,6,7,8,9,10]
    affect_length_set = [2]
    for affect_length in affect_length_set:
        for param in params:
            # plt.rcParams["font.size"] = 5
            for neuron_num in neuron_nums:
                for num_layers in num_layers_set:
                    model = RNN(affect_length,neuron_num,num_layers=num_layers,activation='tanh',bidirectional=True).to(device)
                    fig = plt.figure(figsize=(16.0,8.0/0.96))
                    execute_all("henon",model,neuron_num,num_layers,'tanh',batch_size,affect_length,epochs,param,1.4,learning_rate=0.001)
                    # execute_all("logistic",model,neuron_num,num_layers,'tanh',batch_size,affect_length,epochs,param,4.0,learning_rate=0.001)
