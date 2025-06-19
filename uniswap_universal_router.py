
from web3 import Web3
from eth_account import Account
from eth_abi.codec import ABICodec
from uniswap_universal_router_decoder import FunctionRecipient, RouterCodec
from eth_account.signers.local import LocalAccount
from abi import PERMIT2_ABI, UNIVERSAL_ROUTER_ABI, ERC20_ABI
import time

# 🚀 Uniswap V4 Universal Router Addresses for Each Chain
ROUTER_ADDRESSES = {
    "ethereum": "0x66a9893cc07d91d95644aedd05d03f95e1dba8af",
    "base": "0x6ff5693b99212da76ad316178a184ab56d299b43",  # Replace with Base UniswapV4 router address
    "optimism": "0x851116d9223fabed8e56c0e6b8ad0c31d98b3507",  # Replace with Optimism UniswapV4 router address
    "polygon": "0x1095692a6237d83c6a72f3f5efedb9a670c49223",  # Replace with Polygon UniswapV4 router address
    "arbitrum": "0xa51afafe0263b40edaef0df8781ea9aa03e381a3",  # Replace with Arbitrum UniswapV4 router address
}




class Uniswap:
    def __init__(self, wallet_address, private_key, provider, web3):
        self.w3=web3
        self.wallet_address = wallet_address
        self.private_key = private_key
        self.account = Account.from_key(private_key)
        self.address = Web3.to_checksum_address(wallet_address)  # This is what was missing

        self.w3 = web3 if web3 else Web3(Web3.HTTPProvider(provider))
        assert self.w3.is_connected(), "❌ Web3 connection failed"

        # 🟢 Auto-select correct UniswapV4 Universal Router based on L2
        self.chain = self.get_chain_from_provider(provider)
        if self.chain not in ROUTER_ADDRESSES:
            raise ValueError(f"❌ Unsupported chain: {self.chain}")

        self.router_address = Web3.to_checksum_address(ROUTER_ADDRESSES[self.chain])
        self.router = self.w3.eth.contract(address=self.router_address, abi=UNIVERSAL_ROUTER_ABI)

        self.permit2 = self.w3.eth.contract(address=Web3.to_checksum_address("0x000000000022D473030F116dDEE9F6B43aC78BA3"), abi=PERMIT2_ABI)

        # Check for stuck transaction
        stuck_nonce = self.check_for_stuck_transactions()
        if stuck_nonce is not None:
            print("stuck transaction detected")
            self.cancel_transaction(stuck_nonce)
        else:
            print("No stuck transactions to cancel")
            time.sleep(1)
#        stuck_nonce = 1  # Explicitly set the known stuck nonce
#        self.cancel_transaction(stuck_nonce)


    def get_chain_from_provider(self, provider_url):
        """Detects the blockchain network from the provider URL."""
        if "base" in provider_url:
            return "base"
        elif "optimism" in provider_url:
            return "optimism"
        elif "polygon" in provider_url:
            return "polygon"
        elif "arbitrum" in provider_url:
            return "arbitrum"
        else:
            return "ethereum"

    def get_token_decimals(self, token_address):
        token_contract = self.w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
        return token_contract.functions.decimals().call()

    def approve_permit2(self, token_address, amount):
        """
        Approve the Permit2 contract to spend tokens (one-time approval)
        """
        token_address = Web3.to_checksum_address(token_address)
        token_contract = self.w3.eth.contract(
            address=token_address, 
            abi=ERC20_ABI
        )
        
        # Set max approval amount
        max_approval = 2**256 - 1  # max uint256
        
        # Build approval transaction
        contract_function = token_contract.functions.approve(
            self.permit2.address,
            max_approval
        )
        
        gas_params = self.calculate_gas_parameters(estimated_gas_limit=500000)
        if not gas_params or not gas_params['has_sufficient_balance']:
            return False

        tx_params = contract_function.build_transaction({
            "from": self.account.address,
            "gas": gas_params['estimated_total_wei'],
            "maxPriorityFeePerGas": gas_params['max_priority_fee_per_gas'],
            "maxFeePerGas": gas_params['max_fee_per_gas'],
            "type": 2,
            "chainId": self.w3.eth.chain_id,
            "value": 0,
            "nonce": self.w3.eth.get_transaction_count(self.account.address),
        })
        
        signed_tx = self.w3.eth.account.sign_transaction(tx_params, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"Permit2 token approve transaction hash: {tx_hash.hex()}")
        
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            if receipt.status == 1:
                print("Approval transaction confirmed")
                time.sleep(2)  # Wait for state update
                return True
        except Exception as e:
            print(f"Error waiting for approval: {str(e)}")
        return False

    def create_permit_signature(self, token_address):
        """
        Create a Permit2 signature for a specific transaction (needed for each swap)
        """
        token_address = Web3.to_checksum_address(token_address)
        permit2_contract = self.w3.eth.contract(address=self.permit2.address, abi=PERMIT2_ABI)
        
        p2_amount, p2_expiration, p2_nonce = permit2_contract.functions.allowance(
            self.wallet_address,
            token_address,
            self.router_address
        ).call()
        
        print("p2_amount, p2_expiration, p2_nonce: ", p2_amount, p2_expiration, p2_nonce)
        
        codec = RouterCodec()
        allowance_amount = 2**160 - 1  # max/infinite
        permit_data, signable_message = codec.create_permit2_signable_message(
            token_address,
            allowance_amount,
            codec.get_default_expiration(),
            p2_nonce,
            self.router_address,
            codec.get_default_deadline(),
            self.w3.eth.chain_id,
        )
        signed_message = self.account.sign_message(signable_message)
        return permit_data, signed_message

    def check_permit2_allowance(self, token_address):
        """
        Check if token has already been approved for Permit2
        Returns: True if sufficient allowance exists, False otherwise
        """
        token_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address), 
            abi=ERC20_ABI
        )
        
        # Check allowance for Permit2 contract
        permit2_allowance = token_contract.functions.allowance(
            self.wallet_address,
            self.permit2.address
        ).call()
        
        print(f"Current Permit2 allowance: {permit2_allowance}")
        
        # Check if allowance is effectively infinite (very large number)
        LARGE_APPROVAL_THRESHOLD = 2**200  # Any number larger than this is considered "infinite"
        
        return permit2_allowance > LARGE_APPROVAL_THRESHOLD

    def make_trade(self, from_token, to_token, amount, fee, slippage, pool_version="v3"):
        """
        Execute an exact input swap using Universal Router with RouterCodec.
        
        Args:
            from_token (str): Address of token to swap from
            to_token (str): Address of token to swap to
            amount (int): Amount in wei (already converted to smallest unit)
            fee (int): Fee tier (e.g., 3000 for 0.3%)
            slippage (float): Slippage tolerance in percent
        """
        # Convert addresses to checksum format
        from_token = Web3.to_checksum_address(from_token)
        
        # Check token balance first
        token_contract = self.w3.eth.contract(address=from_token, abi=ERC20_ABI)
        decimals_in = self.get_token_decimals(from_token)
        print(f"Input amount in wei: {amount}")
        print(f"Input amount in token: {amount / (10 ** decimals_in)}")
        print(f"Token decimals: {decimals_in}")

        balance = token_contract.functions.balanceOf(self.wallet_address).call()
        print(f"Token balance in wei: {balance}")
        print(f"Token balance in token: {balance / (10 ** decimals_in)}")
        
        if balance < amount:
            raise ValueError(f"Insufficient balance. Have: {balance / (10 ** decimals_in)}, Need: {amount / (10 ** decimals_in)}")

        # Check for existing Permit2 approval
        has_permit2_allowance = self.check_permit2_allowance(from_token)
        if not has_permit2_allowance:
            print("Permit2 approval needed. Initiating approval...")
            approval_success = self.approve_permit2(from_token, amount)
            if not approval_success:
                print("Failed to get Permit2 approval")
                return None
            time.sleep(2)  # Wait for approval to be mined
        else:
            print("Sufficient Permit2 allowance already exists")
        
        # Create permit signature for the swap
        permit_data, signed_message = self.create_permit_signature(from_token)
        if not permit_data or not signed_message:
            print("Failed to create permit signature")
            return None

        print(f"permit_data: {permit_data}")
        print(f"signed_message: {signed_message}")
        print(f"amount_in_wei: {amount}")

        # Continue with swap logic...
        to_token = Web3.to_checksum_address(to_token)

        # Since amount is already in wei, we don't need to convert it
        amount_in_wei = amount
        
        # Get token decimals for display purposes only
        decimals_in = self.get_token_decimals(from_token)
        print(f"Input amount in wei: {amount_in_wei}")
        print(f"Input amount in token: {amount_in_wei / (10 ** decimals_in)}")
        print(f"Token decimals: {decimals_in}")

        # Initialize codec
        codec = RouterCodec()

        #add slippage and correct min_amount_out with calculation using uniswap quoters
        min_amount_out = 0

        # Get deadline (current block timestamp + 300 seconds)
        deadline = self.w3.eth.get_block("latest")["timestamp"] + 300
        
        if pool_version.lower() == "v3":
            # Encode V3 swap
            encoded_data = (
                codec.encode.chain()
                .permit2_permit(permit_data,
                signed_message)
                .v3_swap_exact_in(
                FunctionRecipient.SENDER,
                amount_in_wei,
                min_amount_out,
                [
                    from_token,
                    fee,
                    to_token,
                ],
                ).build(deadline)
            )
            print(f"amount_in_wei: {amount_in_wei}")
        elif pool_version.lower() == "v4":
            # Encode V4 swap
            tick_spacing = 60  # Default tick spacing, adjust if needed
            
            pool_key = codec.encode.v4_pool_key(
                from_token,
                to_token,
                fee,
                tick_spacing,
            )
            
            # Determine if input is native token (ETH/MATIC)
            is_native_input = from_token.lower() == "0x0000000000000000000000000000000000000000"
            
            encoded_data = (
                codec.encode.chain()
                .v4_swap()
                .swap_exact_in_single(
                    pool_key=pool_key,
                    zero_for_one=True,
                    amount_in=amount_in_wei,
                    amount_out_min=min_amount_out,
                )
                .take_all(to_token, 0)
                .settle_all(from_token, amount_in_wei)
                .build_v4_swap()
                .build_transaction(self.account.address, amount_in_wei if is_native_input else 0, ur_address=self.router_address)
            )
        
        else:
            raise ValueError("Unsupported pool_version. Use 'v3' or 'v4'.")
        
        #calculate gas parameters with estimated gas limit for a permit
        gas_params = self.calculate_gas_parameters(estimated_gas_limit=500000)  # Higher gas limit for swaps
        
        if not gas_params or not gas_params['has_sufficient_balance']:
            return None
        # Build transaction
        tx = {
            "from": self.account.address,
            "to": self.router_address,
            "data": encoded_data,
            "value": amount_in_wei if from_token.lower() == "0x0000000000000000000000000000000000000000" else 0,
            "nonce": self.w3.eth.get_transaction_count(self.account.address),
            "gas": gas_params['estimated_total_wei'],  # Use estimated gas from gas_params
            "maxFeePerGas": gas_params['max_fee_per_gas'],
            "maxPriorityFeePerGas": gas_params['max_priority_fee_per_gas'],
            "type": 2,  # EIP-1559 transaction type
            "chainId": self.w3.eth.chain_id
        }
        
        # Sign and send transaction
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        return tx_hash
  
    def cancel_transaction(self, stuck_nonce):
        """
        Cancel stuck transaction by sending 0 ETH to self
        """
        # First, get the original stuck transaction
        try:

            # Get current gas values
            base_fee = self.w3.eth.get_block("latest")["baseFeePerGas"]
            priority_fee = self.w3.eth.max_priority_fee

            # Apply different multipliers
            base_multiplier = 8   # High multiplier to prevent underpricing
            priority_multiplier = 5  # Lower multiplier for miner tips

            new_max_fee_per_gas = max(base_fee * base_multiplier + priority_fee * 3, Web3.to_wei(0.1, "gwei"))  
            new_max_priority_fee = max(priority_fee * priority_multiplier, Web3.to_wei(0.005, "gwei"))

            # Estimate gas required
            gas_limit = 21000  # Example gas limit for a swap

            # ✅ Correct Total Gas Cost Calculation
            total_gas_wei = gas_limit * new_max_fee_per_gas
            total_gas_eth = Web3.from_wei(total_gas_wei, "ether")

            print(f"🟢 Estimated Total Gas Cost: {total_gas_eth} ETH")
            print(f"🔹 Max Fee per Gas: {Web3.from_wei(new_max_fee_per_gas, 'gwei')} Gwei")
            print(f"🔹 Max Priority Fee per Gas: {Web3.from_wei(new_max_priority_fee, 'gwei')} Gwei")

            # Check if we have enough balance
            balance = self.w3.eth.get_balance(self.account.address)

            print(f"\nCurrent balance: {Web3.from_wei(balance, 'ether')} ETH")
            print(f"Required balance: {(total_gas_eth, 'ether')} ETH")

            if balance < total_gas_wei:
                print(f"ERROR: Insufficient balance for cancellation!")
                print(f"Need {(total_gas_eth - Web3.from_wei(balance), 'ether')} more ETH")
                return

            cancel_tx = {
                "from": self.account.address,
                "to": self.account.address,
                "value": 0,
                "gas": 21000,
                "maxPriorityFeePerGas": new_max_priority_fee,
                "maxFeePerGas": new_max_fee_per_gas,
                "type": 2,
                "chainId": self.w3.eth.chain_id,
                "nonce": stuck_nonce
            }

            print(f"\nAttempting cancellation with:")
            print(f"New Max Fee: {Web3.from_wei(new_max_fee_per_gas, 'gwei')} gwei")
            print(f"New Priority Fee: {Web3.from_wei(new_max_priority_fee, 'gwei')} gwei")

            signed_tx = self.w3.eth.account.sign_transaction(cancel_tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            print(f"Cancellation transaction hash: {tx_hash.hex()}")

        except Exception as e:
            print(f"Error: {str(e)}")
            print("Consider sending more ETH to cover higher gas fees")

    def check_for_stuck_transactions(self):
        """
        Check for stuck transactions by comparing pending vs latest nonce
        Returns: stuck nonce if found, None if no stuck transactions
        """
        try:
            pending_nonce = self.w3.eth.get_transaction_count(self.account.address, 'pending')
            latest_nonce = self.w3.eth.get_transaction_count(self.account.address, 'latest')
            
            print(f"Pending nonce: {pending_nonce}")
            print(f"Latest nonce: {latest_nonce}")
            
            if pending_nonce > latest_nonce:
                print(f"Found stuck transaction with nonce {latest_nonce}")
                return latest_nonce
            else:
                print("No stuck transactions found")
                return None
            
        except Exception as e:
            print(f"Error checking for stuck transactions: {e}")
            return None

    def calculate_gas_parameters(self, estimated_gas_limit=21000):
        """
        Calculate optimal gas parameters and check balance sufficiency.
        
        Args:
            estimated_gas_limit (int): Estimated gas limit for the transaction
        
        Returns:
            dict: Gas parameters and status, or None if insufficient balance
            {
                'max_fee_per_gas': int,
                'max_priority_fee_per_gas': int,
                'estimated_total_wei': int,
                'has_sufficient_balance': bool
            }
        """
        try:
            # Get current gas values 
            base_fee = self.w3.eth.get_block("latest")["baseFeePerGas"]
            priority_fee = self.w3.eth.max_priority_fee

            # More efficient multipliers for Base network
            base_multiplier = 1.2   # Reduced from 2
            priority_multiplier = 1.1  # Reduced from 2

            # Calculate new gas prices (in wei) and convert to integers
            new_max_fee_per_gas = int(base_fee * base_multiplier + priority_fee * priority_multiplier)
            new_max_priority_fee = int(priority_fee * priority_multiplier)

            # Set minimum values for Base (in wei)
            min_max_fee = Web3.to_wei(0.003, 'gwei')  # 0.003 gwei minimum
            min_priority_fee = Web3.to_wei(0.001, 'gwei')  # 0.001 gwei minimum

            # Use maximum between calculated and minimum values
            new_max_fee_per_gas = max(new_max_fee_per_gas, min_max_fee)
            new_max_priority_fee = max(new_max_priority_fee, min_priority_fee)

            # Ensure max fee is higher than priority fee
            if new_max_fee_per_gas < new_max_priority_fee:
                new_max_fee_per_gas = new_max_priority_fee * 2

            # Calculate total gas cost
            total_gas_wei = int(estimated_gas_limit * new_max_fee_per_gas)
            total_gas_eth = Web3.from_wei(total_gas_wei, "ether")

            # Get current balance
            balance = self.w3.eth.get_balance(self.account.address)

            # Print gas details
            print(f"\n🟢 Gas Parameters:")
            print(f"🔹 Max Fee per Gas: {Web3.from_wei(new_max_fee_per_gas, 'gwei')} Gwei")
            print(f"🔹 Max Priority Fee per Gas: {Web3.from_wei(new_max_priority_fee, 'gwei')} Gwei")
            print(f"🔹 Estimated Total Gas Cost: {total_gas_eth} ETH")
            print(f"🔹 Current Balance: {Web3.from_wei(balance, 'ether')} ETH")

            has_sufficient_balance = balance >= total_gas_wei
            if not has_sufficient_balance:
                needed_eth = Web3.from_wei(total_gas_wei - balance, "ether")
                print(f"⚠️ ERROR: Insufficient balance!")
                print(f"⚠️ Need {needed_eth} more ETH")

            return {
                'max_fee_per_gas': int(new_max_fee_per_gas),  # Ensure integer
                'max_priority_fee_per_gas': int(new_max_priority_fee),  # Ensure integer
                'estimated_total_wei': int(estimated_gas_limit),  # Ensure integer
                'has_sufficient_balance': has_sufficient_balance
            }

        except Exception as e:
            print(f"Error calculating gas parameters: {str(e)}")
            return None
