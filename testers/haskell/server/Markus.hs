{- MarkUs Autotesting API for Haskell -}
{-# LANGUAGE DeriveGeneric #-}

module Markus (doTest, doTestWithTimeout) where
import Control.Monad ((>=>))
import Test.QuickCheck -- cabal install quickcheck
import System.Timeout (timeout)
import Data.Aeson hiding (Result, Success) -- cabal install aeson
import GHC.Generics
import qualified Data.ByteString.Lazy.Char8 as C8 (putStrLn, ByteString)
import Data.List (nub, isPrefixOf)
-- import Test.Tasty.Config (Config (..), parseConfig)
-- import Test.Tasty.Discover (findTests) -- cabal install tasty-discover
import Test.Tasty.Generator (Test (..), Generator (..), generators, mkTest)
import System.Environment (getArgs)
import System.Exit (exitFailure)
import System.IO (hPutStrLn, stderr)

timeoutLength :: Int
timeoutLength = 60000000  -- 60 second timeout

quickCheckArgs :: Args
quickCheckArgs = stdArgs { chatty = False }

doTest :: Testable a => String -> a -> IO ()
doTest label test =
  doTestWithTimeout timeoutLength label test

doTestWithTimeout :: Testable a => Int -> String -> a -> IO ()
doTestWithTimeout n label test = do
  resultStr <- showResult label <$> (timeout n . quickCheckWithResult quickCheckArgs) test
  C8.putStrLn resultStr


-- | Extract the test names from discovered modules.
extractTests :: FilePath -> String -> [Test]
extractTests file = mkTestDeDuped . isKnownPrefix . parseTest
  where
    mkTestDeDuped = map (mkTest file) . nub
    isKnownPrefix = filter (\g -> any (checkPrefix g) generators)
    checkPrefix g = (`isPrefixOf` g) . generatorPrefix
    parseTest     = map fst . concatMap lex . lines

-- getTestLabel :: Testable a => a -> String
-- getTestLabel test =
--   print test["testFunction"]

data TestResult = 
  TestResult    { name :: String 
                , status :: String
                , actual :: String
                , expected :: String
                } deriving (Generic, Show)

instance ToJSON TestResult where 
  toEncoding = genericToEncoding defaultOptions 

showResult :: String -> Maybe Result -> C8.ByteString
showResult label (Just (Success _ _ _)) = 
  encode (TestResult label "pass" "" "")
showResult label (Just f@Failure{output=output, theException=Nothing}) = 
  encode (TestResult label "fail" output "")
showResult label (Just f@Failure{output=output, theException=(Just _)}) = 
  encode (TestResult label "error" output "")
showResult label Nothing = 
  encode (TestResult label "error" "" "")

main :: IO ()
main = do
  args <- getArgs
  case args of
    [src] -> do
      print (mkTest src "r")
    _ -> do
      hPutStrLn stderr "Usage: runhaskell Markus.hs test_file"
      exitFailure

