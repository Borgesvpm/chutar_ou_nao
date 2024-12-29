import streamlit as st
import numpy as np
import pandas as pd
import altair as alt

def simulate_exam(num_questions, marked_questions, cutoff, accuracy, correction_factor, num_simulations=10_000):
    # Simulate the performance without guessing
    no_guess_scores = []
    for _ in range(num_simulations):
        correct_answers = np.random.binomial(marked_questions, accuracy)
        wrong_answers = marked_questions - correct_answers
        score = correct_answers - (wrong_answers * correction_factor)
        no_guess_scores.append(score)

    # Simulate the performance with different guessing strategies
    guess_scores = {"1/3": [], "2/3": [], "3/3": []}
    for _ in range(num_simulations):
        correct_answers = np.random.binomial(marked_questions, accuracy)
        unmarked_questions = num_questions - marked_questions

        for fraction, key in zip([1/3, 2/3, 1], ["1/3", "2/3", "3/3"]):
            guessed_questions = int(unmarked_questions * fraction)
            guessed_correct = np.random.binomial(guessed_questions, 1 / 2)  
            guessed_wrong = guessed_questions - guessed_correct

            # Ensure penalties for incorrect guesses are applied correctly
            score = (correct_answers + guessed_correct) - (wrong_answers * correction_factor) - (guessed_wrong * correction_factor)
            guess_scores[key].append(score)

    return no_guess_scores, guess_scores

# Streamlit UI
st.title("É Apropriado Chutar na Prova?")
st.markdown("Esse app faz 10 mil simulações para cada estratégia (chute ou não chute) para averiguar qual é a melhor.")

# Inputs
num_questions = st.number_input(
    "Número de Questões da Prova:",
    min_value=1,
    value=120,
    step=1,
    help="Total de questões presentes na prova."
)

correction_factor = st.number_input(
    "Fator de correção da prova:",
    min_value=0.0,
    value=1.0,
    step=0.01,
    help="Valor descontado por cada resposta errada na prova. Padrão do Cebraspe (+1 para questões certas, -1 para questões erradas)."
)
cutoff = st.number_input(
    "Nota de corte estimada:",
    min_value=0.0,
    value=70.0,
    step=1.0,
    help="Estimativa da pontuação mínima para a aprovação (pode ser estimado com provas similares da mesma banca)."
)
accuracy = st.slider(
    "Sua taxa de acerto:",
    min_value=0.0,
    max_value=1.0,
    value=0.8,
    step=0.01,
    help="Probabilidade de acertar uma questão marcada, estimada por meio de simulados com questões de dificuldade equivalente da banca."
)

marked_questions = st.number_input(
    "Número de questões que você marcou com confiança:",
    min_value=0,
    max_value=num_questions,
    value=60,
    step=1,
    help="Quantidade de questões que você marcou com confiança, após a primeira passada pela prova."
)


# Run Simulation if Inputs are Valid
if st.button("Simular"):
    no_guess_scores, guess_scores = simulate_exam(
        num_questions=num_questions,
        marked_questions=marked_questions,
        cutoff=cutoff,
        accuracy=accuracy,
        correction_factor=correction_factor,
    )

    # Calculate probabilities of being approved
    no_guess_approved = sum(score >= cutoff for score in no_guess_scores)
    no_guess_probability = no_guess_approved / len(no_guess_scores)

    guess_probabilities = {
        key: sum(score >= cutoff for score in scores) / len(scores)
        for key, scores in guess_scores.items()
    }

    # Display Results
    st.write(f"Probabilidade de ser aprovado SEM chutar: {no_guess_probability:.2%}")
    for key, probability in guess_probabilities.items():
        st.write(f"Probabilidade de ser aprovado chutando {key} das questões remanescentes: {probability:.2%}")

    # Determine best strategy
    best_strategy = max(guess_probabilities, key=guess_probabilities.get)
    if guess_probabilities[best_strategy] > no_guess_probability:
        st.success(f"É apropriado chutar {best_strategy} das questões remanescentes!")
    else:
        st.warning("Não é apropriado chutar na prova!")

    # Visualization with Altair
    st.write("Distribuição das Pontuações")
    data = pd.DataFrame({
        "Sem Chutar": no_guess_scores,
        **{f"Chutar {key}": scores for key, scores in guess_scores.items()}
    })
    data_melted = data.melt(var_name="Estratégia", value_name="Pontuação")

    chart = alt.Chart(data_melted).mark_boxplot().encode(
        x="Estratégia:N",
        y="Pontuação:Q",
        color="Estratégia:N"
    ).properties(
        width=600,
        height=400
    )

    st.altair_chart(chart, use_container_width=True)

    st.markdown("*P.S. De modo geral, as estratégias de chute possuem a mesma média, porém a estratégia com o maior número de chutes possuem uma variância maior (ou seja, você pode ir muito bem, mas também pode ir muito mal). Por esse motivo, quando o chute é a melhor opção, de modo geral, chutar todas as questões tende a ser a melhor estratégia.*")
    st.markdown("*Por outro lado, quando você já tem uma performance muito próxima de atingir a nota de corte, não chutar ou chutar pouco tende a ser a melhor estratégia.*")