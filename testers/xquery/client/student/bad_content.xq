declare variable $dataset0 external;

<output>
{
    for $in in $dataset0/input/in
    return <out>{concat(string($in), 'X')}</out>
}
</output>
