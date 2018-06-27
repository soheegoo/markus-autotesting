
{- CSC324 Winter 2018: Exercise 1

*Before starting, please review the exercise guidelines at
https://www.cs.toronto.edu/~david/csc324/homework.html*

This part of the exercise is similar in spirit to the Racket part,
except using the Haskell programming language instead.

We strongly recommend completing the functions in Racket (and
verifying their correctness) first, so that way your work in
this part can be done by translating the syntax of Racket
into Haskell.

The one *new* idea here is the use of the QuickCheck library
to use a different kind of approach to testing called
*property-based testing*. We illustrate a few basic property-based
tests throughout the file.
-}

-- The module definition line, including exports. Don't change this!
module Submission (celsiusToFarenheit, nCopies, numEvens, numManyEvens) where

-- | Imports used for testing purposes only.
import Test.QuickCheck (Property, quickCheck, (==>))


{- Unlike Racket, Haskell is *statically-typed*.
   We'll go into more detail about what this means later in the course,
   but for now we've provided type signatures for the functions here
   to simplify any compiler error messages you might receive.
   (Don't change them; they're required to compile against our tests.)

   NOTE: use the `round` function to convert from floating-point types
   to `Int`.
-}
celsiusToFarenheit :: Float -> Int
celsiusToFarenheit temp =
    32 + round ((9.0/5.0) * temp)

-- | The simplest "property-based test" is simply a unit test in disguise.
prop_celsius0 :: Bool
prop_celsius0 =
    celsiusToFarenheit 0 == 32

prop_celsius37 :: Bool
prop_celsius37 =
    celsiusToFarenheit 37 == 99

-------------------------------------------------------------------------------

{-
For the recursive functions, we recommend doing these in two ways:

  First, write them using `if` expressions, as you would in Racket.

  Then when that works, use *pattern matching* to simplify the definitions
  (http://learnyouahaskell.com/syntax-in-functions#pattern-matching)

Remember: Strings are simply lists of characters. String === [Char]
(http://learnyouahaskell.com/starting-out#an-intro-to-lists)
-}
nCopies :: String -> Int -> String
nCopies _ 0 = ""
nCopies s n = s ++ nCopies s (n - 1)


-- | This is a QuickCheck property that says,
-- "If n >= 0, then when you call nCopies on a string s and int n,
-- the length of the resulting string is equal to
-- n * the length of the original string.
--
-- QuickCheck verifies this property holds for a random selection of
-- inputs (by default, choosing 100 different inputs).
prop_nCopiesLength :: [Char] -> Int -> Property
prop_nCopiesLength s n =
    n >= 0 ==> (length (nCopies s n) == (length s) * n)

-------------------------------------------------------------------------------

-- We've given you a recursive template here to start from.
-- But noted as above, you can later try simplifying this definition using
-- using pattern matching.
numEvens :: [Int] -> Int
-- numEvens numbers =
--     if null numbers
--     then
--         ...
--     else
--         let firstNumber = head numbers
--             numEvensInRest = numEvens (tail numbers)
--         in
--             ...

numEvens numbers =
    if null numbers
    then
        0
    else
        let firstNumber = head numbers
            numEvensInRest = numEvens (tail numbers)
        in
            if firstNumber `mod` 2 == 0
            then
                1 + numEvensInRest
            else
                numEvensInRest


numManyEvens :: [[Int]] -> Int
numManyEvens [] = 0
numManyEvens (firstList : rest) =
    let numManyEvensInRest = numManyEvens rest
    in
        if numEvens firstList >= 3
        then
            1 + numManyEvensInRest
        else
            numManyEvensInRest


-- | This is a property that says,
-- "the number returned by numEvens is less than or equal to
-- the length of the original list."
prop_numEvensLength :: [Int] -> Bool
prop_numEvensLength nums =
    numEvens nums <= length nums


-- | What do you think this property says?
prop_numManyEvensDoubled :: [[Int]] -> Bool
prop_numManyEvensDoubled listsOfNums =
    let doubled = listsOfNums ++ listsOfNums
    in
        numManyEvens doubled == 2 * (numManyEvens listsOfNums)

-------------------------------------------------------------------------------

-- | This main function runs the quickcheck tests.
-- This gets executed when you compile and run this program. We'll talk about
-- "do" notation much later in the course, but for now if you want to add your
-- own tests, just define them above, and add a new `quickcheck` line here.
main :: IO ()
main = do
    quickCheck prop_celsius0
    quickCheck prop_celsius37
    quickCheck prop_nCopiesLength
    quickCheck prop_numEvensLength
    quickCheck prop_numManyEvensDoubled