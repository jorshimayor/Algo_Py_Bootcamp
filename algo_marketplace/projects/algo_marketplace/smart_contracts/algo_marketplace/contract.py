from algopy import ARC4Contract, Asset, Global, Txn, UInt64, arc4, gtxn, itxn


class AlgoMarketplace(ARC4Contract):
    asset_id: UInt64
    unitary_price: UInt64

    # create the app
    @arc4.abimethod(allow_actions=["NoOp"], create="require")
    def create_application(self, asset_id: Asset, unitary_price: UInt64) -> None:
        self.assetId = asset_id.id
        self.unitaryPrice = unitary_price

    # update the listing price
    @arc4.abimethod
    def set_price(self, unitary_price: UInt64) -> None:
        assert Txn.sender == Global.creator_address
        self.unitaryPrice = unitary_price

    # opt in to the listing
    @arc4.abimethod
    def opt_into_asset(self, mbr_pay: gtxn.PaymentTransaction) -> None:
        assert Txn.sender == Global.creator_address
        assert not Global.current_application_address.is_opted_in(Asset(self.asset_id))

        assert mbr_pay.receiver == Global.current_application_address
        assert mbr_pay.amount == Global.min_balance + Global.asset_opt_in_min_balance
        itxn.AssetTransfer(
            xfer_asset=self.asset_id,
            asset_receiver=Global.current_application_address,
            asset_amount=0,
        ).submit()

    # buy the listing
    @arc4.abimethod
    def buy_asset(self, buyer_txn: gtxn.PaymentTransaction, quantity: UInt64) -> None:
        assert self.unitaryPrice != UInt64(0)
        assert Txn.sender == buyer_txn.sender
        assert buyer_txn.receiver == Global.current_application_address
        assert buyer_txn.amount == self.unitaryPrice * quantity

        itxn.AssetTransfer(
            xfer_asset=self.asset_id,
            asset_receiver=Txn.sender,
            asset_amount=quantity,
        ).submit()

    # delete the app
    @arc4.abimethod(allow_actions=["DeleteApplication"])
    def delete_application(self) -> None:
        assert Txn.sender == Global.creator_address

        itxn.AssetTransfer(
            xfer_asset=self.asset_id,
            asset_receiver=Global.creator_address,
            asset_amount=0,
            asset_close_to=Global.creator_address,
        ).submit()

        itxn.Payment(
            receiver=Global.creator_address,
            amount=0,
            close_remainder_to=Global.creator_address,
        ).submit()
