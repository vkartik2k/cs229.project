from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout
from keras import optimizers
import matplotlib.pyplot as plt
import numpy as np
from utils_branch2 import minutizer, combine_ts, preprocess_2


def lstm_model(stocks: list,
               lookback: int = 36,
               epochs: int = 100,
               batch_size: int = 96,
               ground_features: int = 5):
    # Import data_branch2
    data = minutizer(combine_ts(stocks), split=5)

    data = preprocess_2(data, stocks)


    # Transform data_branch2
    n, d = data.shape
    train_val_test_split = {'train': 0.7, 'val': 0.85, 'test': 1}

    X = np.zeros((n - lookback, lookback, d))
    Y = np.zeros((n - lookback, int(d/ground_features)))
    for i in range(X.shape[0]):
        for j in range(d):
            X[i, :, j] = data.iloc[i:(i+lookback), j]
            if j < int(d/ground_features):
                Y[i, j] = data.iloc[lookback + i, j * ground_features]

    X_train = X[0: int(n * train_val_test_split['train'])]
    y_train = Y[0: int(n * train_val_test_split['train'])]

    X_val = X[int(n*train_val_test_split['train']): int(n*train_val_test_split['val'])]
    y_val = Y[int(n*train_val_test_split['train']): int(n*train_val_test_split['val'])]

    #opens_val = opens[int(n*train_val_test_split['train']): int(n*train_val_test_split['val'])]


    # Initialising the RNN_branch2
    model = Sequential()

    # Adding layers. LSTM(n) --> Dropout(p)
    model.add(LSTM(units=1, return_sequences=True, use_bias=True, input_shape=(X_train.shape[1], d)))
    model.add(Dropout(0.1))

    model.add(LSTM(units=2, return_sequences=True, use_bias=False))
    model.add(Dropout(0.1))

    model.add(LSTM(units=int(d/ground_features), return_sequences=False, use_bias=False))
    model.add(Dropout(0.1))

    #model.add(LSTM(units=1, use_bias=False))
    #model.add(Dropout(0.1))

    # Output layer
    #model.add(Dense(units=int(d/ground_features), activation='linear', use_bias=True))

    # Optimizer
    adam_opt = optimizers.adam(lr=0.001, decay=0.99)

    # Compile
    model.compile(optimizer=adam_opt, loss='mean_squared_error')

    print(model.summary())

    # Fit
    history = model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, validation_data=(X_val, y_val))

    # Validate
    predicted_stock_returns = model.predict(X_val)

    for i, ticker in enumerate(stocks):
        #pred = (predicted_stock_returns[:, i] + 1) * opens_val.values[:, i]
        #real = (y_val[:, i] + 1) * opens_val.values[:, i]
        #
        print(history.history['loss'])
        predcted_returns = predicted_stock_returns[:, i].copy()
        actual_returns = y_val[:, i].copy()
        #
        MSE = sum((predcted_returns - actual_returns) ** 2) / y_val.shape[0]
        dummy_mse = sum(actual_returns**2)/(y_val.shape[0])
        print('=========', ticker, '=========')
        print('Dummy MSE:', dummy_mse)
        print('MSE:', MSE)
        print('--')
        pred_zero_one = predicted_stock_returns[:, i]
        pred_zero_one[pred_zero_one > 0] = 1
        pred_zero_one[pred_zero_one < 0] = 0
        print('Predicted ones:', np.mean(pred_zero_one))
        real_zero_one = y_val[:, i]
        real_zero_one[real_zero_one > 0] = 1
        real_zero_one[real_zero_one < 0] = 0
        print('Real ones:', np.mean(real_zero_one))
        TP = np.sum(np.logical_and(pred_zero_one == 1, real_zero_one == 1))
        TN = np.sum(np.logical_and(pred_zero_one == 0, real_zero_one == 0))
        FP = np.sum(np.logical_and(pred_zero_one == 1, real_zero_one == 0))
        FN = np.sum(np.logical_and(pred_zero_one == 0, real_zero_one == 1))
        print('True positive:', TP)
        print('True Negative:', TN)
        print('False positive:', FP)
        print('False Negative:', FN)
        print('Dummy guess true rate:', max(np.mean(real_zero_one), 1 - np.mean(real_zero_one)))
        accuracy = (TP + TN)/(TP + TN + FP + FN)
        print('Accuracy:', max(accuracy, 1 - accuracy))
        print('--')
        obvious_strategy = np.multiply(pred_zero_one, actual_returns)
        dummy_return = 1
        strategy_return = 1
        threshold = np.percentile(predcted_returns, 10)
        for j in range(pred_zero_one.shape[0]):
            dummy_return *= (1 + actual_returns[j])
            if predcted_returns[j] > threshold:
                strategy_return *= (1 + actual_returns[j])
        print('Dummy return:', (dummy_return - 1) * 100)
        print('Dummy standard deviation: ', np.std(actual_returns))
        print('Dummy Sharpe Ration:', np.mean(actual_returns)/np.std(actual_returns))
        print('Strategy return:', (strategy_return - 1) * 100)
        print('Strategy standard deviation: ', np.std(obvious_strategy))
        print('Strategy Sharpe Ration:', np.mean(obvious_strategy) / np.std(obvious_strategy))

        """
        plt.plot(real, color='red', label='Real ' + ticker + ' Stock Price')
        plt.plot(pred, color='blue', label='Predicted ' + ticker + ' Stock Price')
        plt.title(ticker + ' Stock Price Prediction')
        plt.xlabel('Time')
        plt.ylabel(ticker + ' Stock Price')
        plt.legend()
        plt.savefig('../output/RNN_results/LSTM_new_test_' + ticker + '.png')
        plt.close()
        """

        plt.hist(actual_returns, bins=20, label='Real', density=True)
        plt.hist(predcted_returns, bins=20, label='Predicted', density=True)
        plt.title(ticker)
        plt.legend()
        plt.savefig('../output/RNN_results/LSTM_new_test_histogram' + ticker + '.png')
        plt.close()


lstm_model(['AAPL', 'ACN'])