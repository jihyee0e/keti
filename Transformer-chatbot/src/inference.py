import tensorflow as tf
import pickle
from src.model import PositionalEncoding, MultiHeadAttention
from src.mask_schedule import create_padding_mask, create_look_ahead_mask, CustomSchedule

MAX_LENGTH = 40

# tokenizer 불러오기
with open('model/tokenizer.pickle', 'rb') as f:
    tokenizer = pickle.load(f)

# 특수 토큰
START_TOKEN, END_TOKEN = [tokenizer.vocab_size], [tokenizer.vocab_size + 1]

# 간단한 전처리
def preprocess_sentence(sentence):
    sentence = sentence.lower().strip()
    return sentence

# 모델 불러오기
model = tf.keras.models.load_model(
    'model/chatbot_model.keras',
    custom_objects={
        'PositionalEncoding': PositionalEncoding,
        'MultiHeadAttention': MultiHeadAttention,
        'CustomSchedule': CustomSchedule,
        'create_padding_mask': create_padding_mask,
        'create_look_ahead_mask': create_look_ahead_mask
    }
)

def evaluate(sentence):
    sentence = preprocess_sentence(sentence)
    encoded = tokenizer.encode(sentence)

    if not encoded:
        print("⚠️ 입력이 너무 짧거나 처리할 수 없습니다.")
        return tf.constant([])

    sentence = tf.expand_dims(START_TOKEN + encoded + END_TOKEN, axis=0)
    output = tf.expand_dims(START_TOKEN, 0)

    prev_token = None  # 직전 예측 토큰 저장

    for _ in range(MAX_LENGTH):
        predictions = model([sentence, output], training=False)
        predictions = predictions[:, -1:, :]  # 마지막 시점의 결과
        predicted_id = tf.cast(tf.argmax(predictions, axis=-1), tf.int32)

        # 종료 조건 1: EOS 토큰 예측
        if tf.equal(predicted_id, END_TOKEN[0]):
            break

        # 종료 조건 2: 이전 토큰과 같으면 반복 중단
        if prev_token is not None and tf.equal(predicted_id, prev_token):
            print("⚠️ 동일한 토큰 반복 감지. 강제 종료.")
            break

        output = tf.concat([output, predicted_id], axis=-1)
        prev_token = predicted_id  # 현재 토큰을 저장

    return tf.squeeze(output, axis=0)


def predict(sentence):
    prediction = evaluate(sentence)

    if tf.size(prediction).numpy() == 0:
        return "⚠️ 대답할 수 없습니다."

    predicted_sentence = tokenizer.decode([i for i in prediction if i < tokenizer.vocab_size])

    print('Input: {}'.format(sentence))
    print('Output: {}'.format(predicted_sentence))
    
    print("Raw prediction:", prediction.numpy().tolist())
    print("Filtered:", [i for i in prediction if i < tokenizer.vocab_size])

    return predicted_sentence

# 대화 실행
if __name__ == "__main__":
    while True:
        sentence = input("You > ")
        if sentence.lower() == "quit":
            break
        print("Bot >", predict(sentence))