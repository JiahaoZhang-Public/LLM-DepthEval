# LLM-DepthEval: Evaluating GPT-4o for Monocular Depth Estimation

## 🔍 Project Overview

Large language models (LLMs) with multimodal capabilities, such as GPT-4o, have demonstrated impressive generalization across diverse tasks involving both text and visual data. However, these models are primarily trained on general multimodal datasets without explicit fine-tuning for specific visual tasks such as monocular depth estimation.

This project aims to investigate whether GPT-4o inherently possesses the ability to estimate depth from single RGB images without specific training in monocular depth estimation. More broadly, we seek to evaluate if GPT-4o's multimodal training has led to an emergent "world model," allowing it to implicitly grasp physical relationships—particularly spatial and depth relations—through joint learning from RGB images and textual information.

## 🎯 Objectives

Determine if GPT-4o can perform monocular depth estimation without explicit fine-tuning.

Explore the potential of GPT-4o as an implicit "world model," reflecting an understanding of physical relationships within visual scenes.

Assess whether GPT-4o's multimodal learning enables the model to infer accurate spatial relationships from purely visual and textual contexts.

## 🗂 Project Structure

(To be expanded as the project progresses.)

🚀 Quick Start

Install dependencies:

```
pip install -r requirements.txt
```

## 🛠 Methodology

We will evaluate GPT-4o through:

Qualitative analyses of GPT-4o-generated depth maps.

Quantitative benchmarks against established monocular depth estimation datasets.

Comparative analysis with traditional depth estimation models.

## 📌 Future Directions

Extend analysis to other physical understanding tasks.

Investigate transfer learning capabilities of GPT-4o across diverse multimodal tasks.

## 🤝 Collaborators Wanted

We are actively looking for passionate collaborators to join this exploration into the capabilities of GPT-4o in depth estimation and multimodal understanding. Whether your expertise is in computer vision, machine learning, multimodal models, or evaluation methodologies, we'd love to connect with you.
