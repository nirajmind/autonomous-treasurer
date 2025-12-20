# 🛑 Solution to Step 1: The "Mining" Faucet

Instead of proving you are human by holding money, you can prove it by letting your computer do a little work.

1. Go to [Sepolia PoW Faucet](https://sepolia-faucet.pk910.de/).

2. Paste your wallet address. [YOUR_WALLET_ADDRESS]

3. Click "Start Mining".

4. Leave the tab open for about 10-15 minutes. Your computer will calculate hashes [mine](Sepholia-PoW-Mining.png) to earn free Sepolia ETH.

5. Once you have roughly 0.5 Sepolia ETH, stop mining and claim the reward.

6. Then, use the [Soneium Bridge](https://superbridge.app/soneium-minato) to move that ETH to Minato.

# Step 2: Bridge Your Funds

1. Click the link above.

2. Click "Connect" (Top right) and select MetaMask.

3. Check settings:

	From: Sepolia

	To: Soneium Minato

4. Enter Amount: 0.1 ETH.

5. Click "Deposit" (or "Bridge") and confirm in [MetaMask](Bridge-Sepolia-to-Soneium.png).

# Step 3: Mint Your MNEE Tokens (The Final Setup)

You are going to create the token that your AI Treasurer will manage.

1. Open Remix: [Go to](https://remix.ethereum.org/#optimize=false&runs=200&evmVersion=null&version=soljson-v0.8.26+commit.8a97fa7a.js).

2. Create File:

	On the left sidebar, click the "File" icon.

	Click "New File" (or the little document icon).

	Name it: MockMNEE.sol.

3. Paste Code:

```Solidity

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockMNEE is ERC20 {
    constructor() ERC20("Mock MNEE", "MNEE") {
        // Mint 1,000,000 tokens to your wallet
        _mint(msg.sender, 1000000 * 10 ** 18);
    }
}
```

4. Compile:

	Click the "S" icon (Solidity Compiler) on the left bar.

	Click the blue button "Compile MockMNEE.sol".


5. Deploy (Important):

	Click the "ETH Logo" icon (Deploy & Run) on the left bar.

	Environment: Change this to "Injected Provider - MetaMask".
	
	Network Check: Ensure MetaMask is on "Soneium Minato Testnet".
	
	Click the orange "Deploy" button and confirm in MetaMask.
	
	Check the Remix console at the bottom. You should see a green checkmark indicating the transaction succeeded.
	
	Change Environment:

		Click the dropdown that likely says "Remix VM (Cancun)".

		Select "Injected Provider - MetaMask".

👉 CRITICAL: Open your MetaMask extension and switch the network to "Soneium Minato Testnet". (Your bridged ETH should be there by now!).

	Click the orange "Deploy" button.

	Confirm the transaction in MetaMask.
	
```log
Console Output: creation of MockMNEE pending... transaction mined and execution succeed

[Routescan] Verification Failed after 10 attempts: Error: contract does not exist 1946 0x565.......................

```	
*Note: You may see 'Verification Failed' errors in the console. You can safely ignore these; as long as you get a contract address, the deployment worked.*

6. 🏁 Finish Line
	
	Once that deploys, you will see a contract address at the bottom of Remix.(0x565...................................)
	
	Copy the Deployed Contracts address from the bottom left sidebar.

	Copy that Address.

	Update your .env file with it (MNEE_TOKEN_ADDRESS=...).

	Restart Docker (docker-compose up --build).














