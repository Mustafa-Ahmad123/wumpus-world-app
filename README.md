# 🧠 Wumpus Logic Agent

An interactive **AI-based Wumpus World simulator** built using **Python** and **Streamlit**, featuring a **knowledge-based agent** that uses **propositional logic and resolution inference** to navigate safely.

---

## 📌 Project Description

This project implements a **Wumpus World Agent** that can:

* Perceive its environment (breeze, stench, glitter)
* Store knowledge using **CNF clauses**
* Apply **resolution refutation** to infer safe and dangerous cells
* Navigate the grid intelligently

It also includes a **modern interactive UI** for visualization.

---

## 🎯 Key Features

* 🧠 Knowledge-Based AI Agent
* 🔍 Resolution Refutation Inference Engine
* 🌍 Random Wumpus World Generator
* 🎮 Interactive Grid UI (Streamlit)
* 📊 Real-time Metrics & Logs
* 🤖 Auto-navigation (AI decision making)
* ⚠ Safe / Danger / Unknown cell detection

---

## 🛠 Technologies Used

* **Python**
* **Streamlit**
* **HTML/CSS (for UI styling)**
* **Artificial Intelligence Concepts**

---

## 🧩 Project Structure

```
wumpus-logic-agent/
│
├── app.py              # Main Streamlit application
├── logic_engine.py     # Knowledge base + inference engine
├── requirements.txt    # Dependencies
└── README.md           # Project documentation
```

---

## 🧠 AI Concepts Implemented

* **Propositional Logic**
* **Conjunctive Normal Form (CNF)**
* **Resolution Rule**
* **Proof by Refutation**
* **Knowledge-Based Agents**

---

## ⚙️ How It Works

1. The world is randomly generated with:

   * Pits 🕳
   * Wumpus 👾
   * Gold 💰

2. The agent starts at a safe position.

3. It perceives:

   * 💨 Breeze → Pit nearby
   * 💀 Stench → Wumpus nearby
   * ✨ Glitter → Gold found

4. These percepts are added to the **Knowledge Base**.

5. The **Resolution Engine**:

   * Infers safe cells ✅
   * Detects dangerous cells ⚠
   * Marks unknown areas ❓

---

## 🚀 Installation & Run

### 1. Clone the repository

```bash
git clone https://github.com/your-username/wumpus-logic-agent.git
cd wumpus-logic-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

---

## 🎮 Controls

* **Auto Step** → Agent moves automatically
* **Manual Move** → Use directional buttons
* **Reveal All** → Show full world
* **Generate World** → Reset environment

---

## 📊 UI Highlights

* Grid-based world visualization
* Real-time inference logs
* Knowledge base updates
* Metrics:

  * Inference steps
  * Safe cells
  * Danger cells
  * Visited cells

---

## 📈 Future Improvements

* Add arrow shooting for Wumpus
* Implement pathfinding (A*)
* Add probabilistic reasoning
* Improve animations
* Deploy online (Streamlit Cloud)

---

## 🧑‍💻 Author

**Mustafa Ahmad**

---

## ⭐ Contribution

Feel free to fork, improve, and submit pull requests!

---

## 📌 License

This project is for educational purposes.
