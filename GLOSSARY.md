# Order

The different products that were purchased as part of a transaction. This is not referring to the boxes that get sent out by the vendor.

# transaction

A charge to an account of some kind. For example, it could be a credit card transaction. This is the source of truth in the system, as this is what is interacting with the actual exchange of money.

# Line item

A part of an order. This could include one or more items of the same product. For example, if a user orders three notebooks all of the same kind then that would be one line item, with a quantity of three.

The price recorded on a line item is the price of a **single unit**, not the total. The cost of the whole line is `price * quantity` — three notebooks at $4.00 each is a line item with `price = 4.00` and `quantity = 3`, totalling $12.00. This matches how vendors present receipts, and it is what the reconciliation check in `OrderIngestionService` assumes.

# Invoice

This is either a HTML email or PDF that gets processed by the system. This holds all the information necessary to produce the Order and its Line Items.
