from does_the_edge_hold.example import controlled_demos


def test_controlled_demos_show_the_two_failure_modes() -> None:
    report = controlled_demos()
    noise = report["noise_selection"]
    assert noise["development_sharpe"] > noise["median_development_sharpe"]
    assert noise["later_sharpe"] < noise["development_sharpe"]
    assert report["costs"]["gross_pnl_usd"] == 5
    assert report["costs"]["net_pnl_usd"] == -10
    assert report == controlled_demos()
