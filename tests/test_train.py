from src.heart import train


def test_train_placeholder_runs(capsys):
    train.main()
    captured = capsys.readouterr().out
    assert "Train placeholder" in captured
