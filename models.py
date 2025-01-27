# models.py
import numpy as np
from sklearn.linear_model import LinearRegression
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

def analyze_trend(temperatures: list) -> str:
    """Анализирует тенденцию изменения температуры."""
    if len(temperatures) < 2:
        return "Недостаточно данных для анализа."

    X = np.arange(len(temperatures)).reshape(-1, 1)
    y = np.array(temperatures)
    model = LinearRegression()
    model.fit(X, y)
    trend = model.coef_[0]

    if trend > 0:
        return "Температура повышается."
    elif trend < 0:
        return "Температура понижается."
    else:
        return "Температура стабильна."

def create_lstm_model():
    """Создает LSTM модель для предсказания температуры."""
    model = Sequential()
    model.add(LSTM(50, activation="relu", input_shape=(10, 1)))
    model.add(Dense(1))
    model.compile(optimizer="adam", loss="mse")
    return model

def predict_future_temperatures(temperatures: list, days: int = 3) -> list:
    """Предсказывает температуру на следующие дни."""
    if len(temperatures) < 10:
        return []

    model = create_lstm_model()
    X = np.array(temperatures[-10:]).reshape(1, 10, 1)
    predictions = []
    for _ in range(days):
        pred = model.predict(X, verbose=0)[0][0]
        predictions.append(pred)
        X = np.append(X[:, 1:, :], [[[pred]]], axis=1)
    return predictions