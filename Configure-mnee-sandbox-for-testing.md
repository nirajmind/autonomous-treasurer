PS C:\Users\nadhi\source-repos\autonomous-treasurer\backend> npm i -g @mnee/cli

added 152 packages in 23s

53 packages are looking for funding
  run `npm fund` for details
PS C:\Users\nadhi\source-repos\autonomous-treasurer\backend> mnee create
√ Select wallet environment: Sandbox
√ Enter a name for your sandbox wallet: treasurer-dev
√ Set a password for your wallet: ************* (kW4b^M&ju1234)
√ Confirm your password: *************
✅ Wallet created successfully!

   ╭──────────────  New Wallet Created  ───────────────╮
   │                                                   │
   │   💰 Wallet Details                               │
   │                                                   │
   │   • Name: treasurer-dev                           │
   │   • Environment: sandbox                          │
   │   • Address: 1HE5NHdy2n65sgGwBNWMLJPcfg1GtmiCWe   │
   │                                                   │
   │   ✓ This wallet is now active                     │
   │                                                   │
   ╰───────────────────────────────────────────────────╯


PS C:\Users\nadhi\source-repos\autonomous-treasurer\backend> mnee login
🔐 Starting authentication flow...
Press Ctrl+C to cancel at any time.


Opening browser for authentication...
If the browser doesn't open, visit: https://developer.mnee.net/cli/auth?state=uTqj6Bh9EaLViSHndRBfl0pOotAQadshacQRRLc_PX4&redirect=http%3A%2F%2Flocalhost%3A8900%2Fcallback

✅ Successfully authenticated as niky.sway@gmail.com

   ╭────────────────  Welcome  ─────────────────╮
   │                                            │
   │   🔓 Authentication Complete               │
   │                                            │
   │   • Logged in as: niky.sway@gmail.com      │
   │                                            │
   │   Available commands:                      │
   │     mnee faucet - Request sandbox tokens   │
   │     mnee whoami - Show current user        │
   │     mnee logout - Sign out                 │
   │                                            │
   ╰────────────────────────────────────────────╯

PS C:\Users\nadhi\source-repos\autonomous-treasurer\backend> mnee balance
√ Balance retrieved!

   ╭───────────────  Balance  ────────────────╮
   │                                          │
   │   💵 Wallet Balance                      │
   │                                          │
   │   $0 MNEE                                │
   │                                          │
   │   💰 treasurer-dev                       │
   │   → 1HE5NHdy2n65sgGwBNWMLJPcfg1GtmiCWe   │
   │                                          │
   ╰──────────────────────────────────────────╯
   
PS C:\Users\nadhi\source-repos\autonomous-treasurer\backend> mnee faucet
Using active wallet address: 1HE5NHdy2n65sgGwBNWMLJPcfg1GtmiCWe
❌ You have already requested tokens in the last 24 hours. Try again in 23 hours and 59 minutes.   