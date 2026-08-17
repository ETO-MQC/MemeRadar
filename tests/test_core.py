import tempfile, unittest
from pathlib import Path
from app.scoring import candidate_score
from app.storage import Storage
from app.execution.paper import PaperExecutor

class CoreTests(unittest.TestCase):
    def test_score_risk_fail_caps(self):
        c={"liquidity_usd":100000,"volume_h1":100000,"buys_m5":100,"sells_m5":5,"age_minutes":10,"change_h1":80}
        s,_=candidate_score(c,95,"fail"); self.assertLessEqual(s,25)
    def test_paper_buy(self):
        with tempfile.TemporaryDirectory() as td:
            st=Storage(Path(td)/"t.db"); cfg={"paper":{"starting_balance_usdt":50,"max_open_positions":8},"collector":{"hard_stop_loss_pct":40,"recover_principal_at_pct":100,"recover_fraction":.5,"moonbag_trailing_stop_pct":30},"dip":{"take_profit_pct":10,"stop_loss_pct":6,"trailing_start_pct":6,"trailing_stop_pct":4}}
            ex=PaperExecutor(st,cfg); c={"token_key":"solana:x","chain":"solana","symbol":"X"}; pid=ex.buy(c,"collector",1,0.01); self.assertTrue(pid>0); self.assertEqual(len(st.list_positions(True)),1)
if __name__=='__main__':unittest.main()
