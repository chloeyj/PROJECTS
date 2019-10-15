import numpy as np
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from collections import deque
import random

class Agent:
    def __init__(self, state_size, window_size, trend, skip, batch_size):
        self.state_size = state_size
        self.window_size = window_size
        self.half_window = window_size // 2
        self.trend = trend
        self.features = self.__scale_feature(trend)
        self.skip = skip
        self.action_size = 3
        self.batch_size = batch_size
        self.memory = deque(maxlen=1000)
        self.inventory = []

        self.gamma = 0.95
        self.epsilon = 0.5
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.999

        tf.reset_default_graph()
        self.sess = tf.InteractiveSession()
        self.X = tf.placeholder(tf.float32, [None, self.state_size])
        self.Y = tf.placeholder(tf.float32, [None, self.action_size])
        feed = tf.layers.dense(self.X, 256, activation=tf.nn.relu)
        self.logits = tf.layers.dense(feed, self.action_size)
        self.cost = tf.reduce_mean(tf.square(self.Y - self.logits))
        self.optimizer = tf.train.GradientDescentOptimizer(1e-5).minimize(self.cost)
        self.sess.run(tf.global_variables_initializer())

    def _set_session(self, sess):
        self.sess = sess

    def __scale_feature(self, trend):
        features = trend.copy()
        scaler = MinMaxScaler()
        features = scaler.fit_transform(features)
        return features.tolist()

    def act(self, state):
        if random.random() <= self.epsilon:
            return random.randrange(self.action_size)
        return np.argmax(self.sess.run(self.logits, feed_dict={self.X: state})[0])

    def predict_action(self, state):
        return np.argmax(self.sess.run(self.logits, feed_dict={self.X: state})[0])

    def get_state(self, t):
        window_size = self.window_size + 1
        d = t - window_size + 1
        block = self.features[d:t + 1] if d >= 0 else -d * [self.features[0]] + self.features[0:t + 1]
        res = []
        for i in range(window_size - 1):
            row = np.array(block[i + 1]) - np.array(block[i])
            for r in row.tolist():
                res.append(r)
        return np.array([res])

    def replay(self, batch_size):
        mini_batch = []
        l = len(self.memory)
        for i in range(l - batch_size, l):
            mini_batch.append(self.memory[i])
        replay_size = len(mini_batch)
        X = np.empty((replay_size, self.state_size))
        Y = np.empty((replay_size, self.action_size))
        states = np.array([a[0][0] for a in mini_batch])
        new_states = np.array([a[3][0] for a in mini_batch])
        Q = self.sess.run(self.logits, feed_dict={self.X: states})
        Q_new = self.sess.run(self.logits, feed_dict={self.X: new_states})
        for i in range(len(mini_batch)):
            state, action, reward, next_state, done = mini_batch[i]
            target = Q[i]
            target[action] = reward
            if not done:
                target[action] += self.gamma * np.amax(Q_new[i])
            X[i] = state
            Y[i] = target

        cost, _ = self.sess.run(
            [self.cost, self.optimizer], feed_dict={self.X: X, self.Y: Y}
        )
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        return cost

    def buy(self, initial_money, close):
        starting_money = initial_money
        states_sell = []
        states_buy = []
        inventory = []
        buy_list = []
        state = self.get_state(0)
        for t in range(0, len(self.trend) - 1, self.skip):
            action = self.predict_action(state)
            next_state = self.get_state(t + 1)

            if action == 1 and len(buy_list) <= 0 and initial_money >= self.trend[t][0] and t < (
                    len(self.trend) - self.half_window):
                inventory.append(self.trend[t][0])
                initial_money -= self.trend[t][0]
                states_buy.append(t)
                buy_list.append('ok')
                print('day %d: buy 1 unit at price %f, total balance %f' % (t, self.trend[t][0], initial_money))

            elif action == 2 and len(buy_list) > 0 and len(inventory):
                bought_price = inventory.pop(0)
                initial_money += self.trend[t][0]
                states_sell.append(t)
                buy_list = []
                try:
                    invest = ((close[t] - bought_price) / bought_price) * 100
                except:
                    invest = 0
                # print('day %d, sell 1 unit at price %f, investment %f%%, total balance %f' % (
                #     t, close[t], invest, initial_money))

            state = next_state
        invest = ((initial_money - starting_money) / starting_money) * 100
        total_gains = initial_money - starting_money
        return states_buy, states_sell, total_gains, invest

    def train(self, iterations, checkpoint, initial_money):
        for i in range(iterations):
            total_profit = 0
            inventory = []
            buy_list = []
            state = self.get_state(0)
            # print("train state: ", state.shape)
            starting_money = initial_money
            for t in range(0, len(self.trend) - 1, self.skip):
                # print("T: ", t)
                action = self.act(state)
                next_state = self.get_state(t + 1)

                if action == 1 and len(buy_list) <= 0 and starting_money > self.trend[t][0] and t < (
                        len(self.trend) - self.half_window):
                    inventory.append(self.trend[t][0])
                    starting_money -= self.trend[t][0]
                    buy_list.append('ok')

                elif action == 2 and len(buy_list) > 0 and len(inventory) > 0:
                    bought_price = inventory.pop(0)
                    total_profit += self.trend[t][0] - bought_price
                    starting_money += self.trend[t][0]
                    buy_list = []

                invest = ((starting_money - initial_money) / initial_money)
                self.memory.append((state, action, invest,
                                    next_state, starting_money < initial_money))
                state = next_state
                batch_size = min(self.batch_size, len(self.memory))
                cost = self.replay(batch_size)
            if (i + 1) % checkpoint == 0:
                print('epoch: %d, total rewards: %f.3, cost: %f, total money: %f' % (i + 1, total_profit, cost,
                                                                                     starting_money))
