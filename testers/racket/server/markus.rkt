#!/usr/bin/env racket
#lang racket

(require rackunit)
(require rackunit/text-ui)
(require rackunit/private/check-info)
(require json)
(require racket/cmdline)
(require syntax/modcode)

(define-syntax-rule (require-names path name ...)
  (begin
    (require path)
    (if-defined name
                (void)
                (define (name) (error (format "Name ~a could not be imported" (quote name)))))
    ...))
  
; For testing
(struct markus-result (name status actual expected))

(define (markus-result->hash r) 
  (hasheq 'name (markus-result-name r)
          'status (markus-result-status r)
          'actual (markus-result-actual r)
          'expected (markus-result-expected r)))

(define (check-infos->hash stack)
  (make-immutable-hash
   (map (lambda (ci) (cons (check-info-name ci) (check-info-value ci))) stack)))

(define (make-success test-case-name result)
  (markus-result->hash 
    (markus-result test-case-name "pass" "" "")))

(define (make-failure test-case-name result)
  (let* ( [failure-data
            (if (exn:test:check? result)
              (check-infos->hash (exn:test:check-stack result))
              (hash))]
          [actual (hash-ref failure-data 'actual "<void>")]
          [expected (hash-ref failure-data 'expected "<void>")])
        (markus-result->hash
          (markus-result 
            test-case-name 
            "fail" 
            (format "~s" (if (pretty-info? actual) (pretty-info-value actual) actual))
            (format "~s" (if (pretty-info? expected) (pretty-info-value expected) expected))))))

(define (make-error test-case-name result)
  (markus-result->hash 
    (markus-result test-case-name "error" (format "~s" (exn-message result)) "")))

(define (show-test-result result)
  (match result
    [(test-success test-case-name result) (make-success test-case-name result)]
    [(test-failure test-case-name result) (make-failure test-case-name result)]
    [(test-error test-case-name result) (make-error test-case-name result)]))

(define (raise-markus-error message [error-type 'markus-error])
  (raise (error error-type message)))

(module+ main
  (define test-suite-sym 'all-tests)
  (define test-file 
    (command-line 
      #:program "compiler"
      #:once-each
      [("-t" "--test-suite") ts "Name of the test suite to run in the test-file"
                                (set! test-suite-sym (string->symbol ts))]
      #:args (test-file)
      test-file))
  
  (define test-results null)
  (let  ([s (current-error-port)])
        (parameterize ([current-output-port s])
          (set! test-results 
            (run-test (dynamic-require/expose (string->path test-file) test-suite-sym)))))
  (write-json (map show-test-result test-results)))
    
