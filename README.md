# GenSurv
## About
GenSurv (Generative Survey) は生成AIを活用し、文献調査を効率化する手法の探索・確立を目指す有志による活動です。現在、具体的には以下のような取り組みを行っています。
- 対話しながらユーザーの求める情報を深掘りし、適切な文献を取得し要約を回答するエージェントの開発
- 文献情報をベクトル化することで先行研究がアプローチしていない領域の可視化
- 文献情報をベクトルデータベースに格納し、それらを根拠にユーザーの質問に回答するシステムの開発

プロジェクトの詳細や過去の活動、参加方法については[こちら](https://gensurv.notion.site/GenSurv-080bd169f48849568ef001a4aa08ca1e?pvs=4)をご確認ください。

## Setup
環境変数
```shell
cp .env.sample .env  # APIキーなどを自分のものに書き換える
brew install direnv
direnv allow
```

Python環境
```shell
pip install -r requirements.txt
```
